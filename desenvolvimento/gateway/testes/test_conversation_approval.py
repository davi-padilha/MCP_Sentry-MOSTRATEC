"""Prototype consent gates and real stdio one-call execution (fixture consent)."""
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import test_gateway_universal as fixtures
from mcp_sentry_gateway.core import approve
from mcp_sentry_gateway.gateway import StdioGateway
from mcp_sentry_gateway.review import CONVERSATION_CONFIRMATION, ensure_pending, security_status, submit_verdict


class ConversationApprovalTests(unittest.TestCase):
    setUp = fixtures.UniversalGatewayTests.setUp
    save_manifest = fixtures.UniversalGatewayTests.save_manifest
    request = staticmethod(fixtures.UniversalGatewayTests.request)

    def prepare(self):
        if not (self.state / "versao-aprovada.json").exists():
            approve(self.manifest, self.state)
        self.original = (self.state / "versao-aprovada.json").read_bytes()
        (self.project / "server.py").write_text(fixtures.SERVER_SOURCE + "\n# benign fixture update\n", encoding="utf-8")
        self.review = StdioGateway(self.manifest, self.state, interface="review", conversation_approval=True)
        self.execution = StdioGateway(self.manifest, self.state, interface="execution", conversation_approval=True)
        self.addCleanup(self.execution.backend.close)
        self.evidence = self.tool(self.review, "sentry_review_current_block", {})["structuredContent"]
        self.verdict = {
            "review_id": self.evidence["review_id"], "reviewed_hash": self.evidence["current_hash"],
            "dossier_hash": self.evidence["dossier_hash"], "policy_version": self.evidence["policy_version"],
            "decision": "allow", "justification": "Technical fixture, not a model review", "risks": [],
        }
        self.authorization = {k: self.verdict[k] for k in ("review_id", "reviewed_hash", "dossier_hash")}
        self.authorization["confirmation"] = CONVERSATION_CONFIRMATION

    def tool(self, gateway, name, arguments):
        return gateway.handle(self.request(1, "tools/call", {"name": name, "arguments": arguments}))["result"]

    def record(self, decision="allow"):
        return self.tool(self.review, "sentry_record_assessment", {"verdict": {**self.verdict, "decision": decision}})

    def echo(self):
        return self.tool(self.execution, "echo", {"value": "ok"})

    def assert_denied(self, result):
        self.assertEqual(result["structuredContent"]["status"], "security_blocked")
        self.assertEqual(self.execution.backend.lifecycle.snapshot()["spawn_attempts"], 0)

    def test_opt_in_catalog_and_interface_separation(self):
        self.prepare()
        default = StdioGateway(self.manifest, self.state, interface="review")
        names = lambda gateway: [t["name"] for t in gateway.handle(self.request(2, "tools/list"))["result"]["tools"]]
        self.assertNotIn("sentry_authorize_once", names(default))
        self.assertIn("sentry_authorize_once", names(self.review))
        self.assertNotIn("sentry_authorize_once", names(self.execution))
        self.assertTrue(self.tool(default, "sentry_authorize_once", self.authorization)["isError"])
        self.assertIsNone(self.review.backend)

    def test_allow_alone_blocks_then_confirmation_runs_once_without_promoting_baseline(self):
        self.prepare()
        result = self.record()["structuredContent"]
        self.assertEqual(result["required_user_confirmation"], CONVERSATION_CONFIRMATION)
        self.assert_denied(self.echo())
        authorized = self.tool(self.review, "sentry_authorize_once", self.authorization)
        self.assertEqual(authorized["structuredContent"]["status"], "allowed_once")
        self.assertEqual(self.execution.backend.lifecycle.snapshot()["spawn_attempts"], 0)
        record, _ = ensure_pending(self.manifest, self.state)
        self.assertEqual(record["approval_source"], "client_attested_user_confirmation")
        self.assertEqual(record["user_confirmation"], CONVERSATION_CONFIRMATION)
        report = (self.state / "relatorios-de-seguranca" / f"operator-approval-{record['review_id']}.txt").read_text(encoding="utf-8")
        self.assertIn("client_attested_user_confirmation", report)
        self.assertNotIn("approval: external_operator_attested", report)
        self.assertEqual(self.echo()["content"][0]["text"], "ok")
        self.assertEqual(self.execution.backend.lifecycle.snapshot()["spawn_attempts"], 1)
        self.assertEqual(self.echo()["structuredContent"]["status"], "security_blocked")
        self.assertTrue(self.tool(self.review, "sentry_authorize_once", self.authorization)["isError"])
        self.assertEqual((self.state / "versao-aprovada.json").read_bytes(), self.original)

    def test_concurrent_protected_calls_cannot_share_one_authorization(self):
        self.prepare()
        self.record()
        self.tool(self.review, "sentry_authorize_once", self.authorization)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.echo(), range(2)))
        self.assertEqual(sum(r.get("content", [{}])[0].get("text") == "ok" for r in results), 1)
        self.assertEqual(sum(r.get("structuredContent", {}).get("status") == "security_blocked" for r in results), 1)
        self.assertEqual(self.execution.backend.lifecycle.snapshot()["spawn_attempts"], 1)

    def test_confirmation_missing_invalid_or_extra_fields_never_authorize(self):
        self.prepare()
        self.record()
        for arguments in ({k: v for k, v in self.authorization.items() if k != "confirmation"},
                          {**self.authorization, "confirmation": "sim"},
                          {**self.authorization, "automatic": True}):
            with self.subTest(arguments=arguments):
                self.assert_denied(self.tool(self.review, "sentry_authorize_once", arguments))

    def test_no_assessment_and_block_verdict_never_authorize(self):
        self.prepare()
        self.assert_denied(self.tool(self.review, "sentry_authorize_once", self.authorization))
        self.record("block")
        self.assert_denied(self.tool(self.review, "sentry_authorize_once", self.authorization))
        self.assert_denied(self.echo())

    def test_requires_client_assessment_not_local_fixture(self):
        self.prepare()
        submit_verdict(self.manifest, self.state, self.verdict)
        self.assert_denied(self.tool(self.review, "sentry_authorize_once", self.authorization))

    def test_awaiting_status_without_positive_bound_verdict_is_insufficient(self):
        self.prepare()
        self.record("block")
        path = self.state / "revisoes-de-atualizacoes" / (self.verdict["review_id"] + ".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["status"] = "awaiting_human_approval"
        path.write_text(json.dumps(record), encoding="utf-8")
        result = self.tool(self.review, "sentry_authorize_once", self.authorization)
        self.assert_denied(result)
        self.assertIn("parecer allow", result["structuredContent"]["reason"])

    def test_expired_authorization_never_starts_backend(self):
        self.prepare()
        self.record()
        self.tool(self.review, "sentry_authorize_once", self.authorization)
        path = self.state / "revisoes-de-atualizacoes" / (self.verdict["review_id"] + ".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["operator_approved_at"] = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
        path.write_text(json.dumps(record), encoding="utf-8")
        result = self.echo()
        self.assertEqual(result["structuredContent"]["status"], "security_review_required")
        self.assertEqual(self.execution.backend.lifecycle.snapshot()["spawn_attempts"], 0)

    def test_stale_identifiers_and_changed_code_are_refused(self):
        self.prepare()
        self.record()
        for key in ("review_id", "reviewed_hash", "dossier_hash"):
            self.assert_denied(self.tool(self.review, "sentry_authorize_once", {**self.authorization, key: "0" * 64}))
        (self.project / "server.py").write_text(fixtures.SERVER_SOURCE + "\n# newer update\n", encoding="utf-8")
        self.assert_denied(self.tool(self.review, "sentry_authorize_once", self.authorization))

    def test_envelope_changes_cannot_be_promoted_by_conversation(self):
        self.prepare()
        self.manifest_data["configuration"]["passthrough_names"] = ["OTHER_ENV"]
        self.save_manifest()
        evidence = self.tool(self.review, "sentry_review_current_block", {})["structuredContent"]
        self.verdict.update(review_id=evidence["review_id"], reviewed_hash=evidence["current_hash"], dossier_hash=evidence["dossier_hash"])
        self.record()
        args = {k: self.verdict[k] for k in ("review_id", "reviewed_hash", "dossier_hash")}
        result = self.tool(self.review, "sentry_authorize_once", {**args, "confirmation": CONVERSATION_CONFIRMATION})
        self.assert_denied(result)
        self.assertIn("envelope", result["structuredContent"]["reason"])

    def test_expired_allow_is_refused(self):
        self.prepare()
        self.record()
        path = self.state / "revisoes-de-atualizacoes" / (self.verdict["review_id"] + ".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["decided_at"] = (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat()
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assert_denied(self.tool(self.review, "sentry_authorize_once", self.authorization))

    def test_authorization_expiry_counts_from_confirmation_not_assessment(self):
        self.prepare()
        self.record()
        path = self.state / "revisoes-de-atualizacoes" / (self.verdict["review_id"] + ".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["decided_at"] = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(self.tool(self.review, "sentry_authorize_once", self.authorization)["structuredContent"]["status"], "allowed_once")
        self.assertEqual(security_status(self.manifest, self.state)["status"], "allowed_once")
        self.assertEqual(self.echo()["content"][0]["text"], "ok")

    def test_existing_backend_copy_requires_reconnection_before_once(self):
        approve(self.manifest, self.state)
        old = StdioGateway(self.manifest, self.state, interface="execution", conversation_approval=True)
        self.addCleanup(old.backend.close)
        self.assertEqual(self.tool(old, "echo", {"value": "old"})["content"][0]["text"], "old")
        self.prepare()
        self.record()
        self.tool(self.review, "sentry_authorize_once", self.authorization)
        blocked = self.tool(old, "echo", {"value": "new"})
        self.assertEqual(blocked["structuredContent"]["status"], "security_blocked")
        self.assertIn("reconecte", blocked["structuredContent"]["reason"])
        self.assertEqual(security_status(self.manifest, self.state)["status"], "allowed_once")
        self.assertEqual(self.echo()["content"][0]["text"], "ok")


if __name__ == "__main__":
    unittest.main()
