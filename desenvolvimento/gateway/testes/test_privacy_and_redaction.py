"""Regression coverage for evidence fidelity and operator-owned privacy rules."""
import ast
import copy
import json
import re
import shutil
import unittest
from pathlib import Path

import test_gateway_universal as fixtures
from mcp_sentry_gateway.core import (
    SentryError, accept_current, approve, inspect, load, load_execution_envelope,
    promote_execution_envelope, safe_text,
)
from mcp_sentry_gateway.gateway import StdioGateway
from mcp_sentry_gateway.mcp_facade import CURRENT_REVIEW_OUTPUT_SCHEMA, PENDING_OUTPUT_SCHEMA
from mcp_sentry_gateway.review import POLICY_VERSION, ensure_pending, get_pending, submit_verdict


POLICY = {
    "schema_version": 1,
    "policy_id": "fixture-privacy-v1",
    "rules": [{
        "rule_id": "public-output",
        "tools": ["echo"],
        "output_scope": "response",
        "allowed_fields": ["value"],
        "restricted_fields": ["attendees", "description"],
        "requirement": "Return only the requested public value; do not disclose private notes.",
    }],
}


class RedactionTests(unittest.TestCase):
    def test_marker_literals_keep_classes_and_valid_python(self):
        source = ('SENSITIVE_MARKERS = ("password=", "token=")\n\n'
                  'class Input:\n    repo_path: str\n\n'
                  'class Log:\n    description = "Start timestamp"\n')
        for ending in ("\n", "\r\n"):
            with self.subTest(ending=repr(ending)):
                raw = source.replace("\n", ending)
                displayed = safe_text(raw.encode())
                self.assertEqual(displayed, raw)
                self.assertEqual([x.name for x in ast.parse(displayed).body if isinstance(x, ast.ClassDef)], ["Input", "Log"])

    def test_quoted_keys_and_bare_assignments_hide_values_preserve_delimiters(self):
        for source in ('password="FAKE_SECRET"', "password='FAKE_SECRET'",
                       '"access_token": "FAKE_SECRET"', "'clientSecret': 'FAKE_SECRET'",
                       'const api_key = "FAKE_SECRET";', 'TOKEN=FAKE_SECRET # public comment'):
            with self.subTest(source=source):
                output = safe_text(source.encode())
                self.assertNotIn("FAKE_SECRET", output)
                self.assertIn("[REDACTED]", output)
                self.assertEqual(output.count('"'), source.count('"'))
                self.assertEqual(output.count("'"), source.count("'"))

    def test_json_nested_secrets_still_redacted(self):
        raw = '{"auth": {"password": "FAKE_SECRET", "refreshToken": "FAKE_REFRESH"}, "public": "ok"}'
        displayed = json.loads(safe_text(raw.encode()))
        self.assertEqual(displayed, {"auth": {"password": "[REDACTED]", "refreshToken": "[REDACTED]"}, "public": "ok"})

    def test_multiline_triple_strings_preserve_line_boundaries(self):
        source = 'password = """\nFAKE_FIRST\nFAKE_SECOND\n"""\nclass Preserved:\n    value = 1\n'
        for ending in ("\n", "\r\n"):
            raw = source.replace("\n", ending)
            displayed = safe_text(raw.encode())
            self.assertNotIn("FAKE_FIRST", displayed)
            self.assertNotIn("FAKE_SECOND", displayed)
            self.assertEqual(re.findall(r"\r\n|\r|\n", displayed), re.findall(r"\r\n|\r|\n", raw))
            self.assertIn("class Preserved:", displayed)
            ast.parse(displayed)

    def test_escaped_quote_does_not_leave_tail_of_secret(self):
        raw = r'password = "FAKE\"TAIL"; public = "ok"'
        output = safe_text(raw.encode())
        self.assertNotIn("FAKE", output)
        self.assertNotIn("TAIL", output)
        self.assertIn('public = "ok"', output)
        ast.parse(output)

    def test_pem_private_key_preserves_headers_and_line_count(self):
        source = 'public\r\n-----BEGIN RSA PRIVATE KEY-----\r\nFAKE_ONE\r\nFAKE_TWO\r\n-----END RSA PRIVATE KEY-----\r\nclass Preserved:\r\n'
        output = safe_text(source.encode())
        self.assertNotIn("FAKE_ONE", output)
        self.assertNotIn("FAKE_TWO", output)
        self.assertIn('-----BEGIN RSA PRIVATE KEY-----\r\n', output)
        self.assertIn('-----END RSA PRIVATE KEY-----\r\nclass Preserved:', output)
        self.assertEqual(output.count('\r\n'), source.count('\r\n'))

    def test_sensitive_words_without_assignment_are_not_values(self):
        source = 'password_names = ["password=", "token=", "api_key", "authorization"]\n'
        self.assertEqual(safe_text(source.encode()), source)


class PrivacyTests(unittest.TestCase):
    setUp = fixtures.UniversalGatewayTests.setUp
    save_manifest = fixtures.UniversalGatewayTests.save_manifest
    request = staticmethod(fixtures.UniversalGatewayTests.request)

    def prepare(self):
        self.manifest_data["privacy_policy"] = copy.deepcopy(POLICY)
        self.save_manifest()
        approve(self.manifest, self.state)
        (self.project / "server.py").write_text(fixtures.SERVER_SOURCE + "\n# update\n", encoding="utf-8")

    def verdict(self, record):
        return {"review_id": record["review_id"], "reviewed_hash": record["dossier"]["current_hash"],
                "dossier_hash": record["dossier"]["dossier_hash"], "policy_version": POLICY_VERSION,
                "decision": "allow", "justification": "Synthetic technical fixture", "risks": []}

    def test_advertised_assessment_schema_records_current_policy_without_execution(self):
        self.prepare()
        for decision in ("allow", "block"):
            with self.subTest(decision=decision):
                state = self.temp / ("schema-" + decision)
                shutil.copytree(self.state, state)
                gateway = StdioGateway(self.manifest, state, interface="review")
                try:
                    tools = gateway.handle(self.request(1, "tools/list", {}))["result"]["tools"]
                    tool = next(x for x in tools if x["name"] == "sentry_record_assessment")
                    advertised = tool["inputSchema"]["properties"]["verdict"]["properties"]["policy_version"]["const"]
                    gateway.handle(self.request(2, "tools/call", {"name": "sentry_review_current_block", "arguments": {}}))
                    record, _ = ensure_pending(self.manifest, state)
                    self.assertEqual(advertised, record["policy_version"])
                    verdict = self.verdict(record)
                    verdict.update(policy_version=advertised, decision=decision)
                    response = gateway.handle(self.request(3, "tools/call", {
                        "name": "sentry_record_assessment", "arguments": {"verdict": verdict},
                    }))["result"]["structuredContent"]
                    self.assertEqual(response["status"], "awaiting_human_approval" if decision == "allow" else "blocked")
                    self.assertIsNone(gateway.backend)
                finally:
                    if gateway.backend is not None:
                        gateway.backend.close()

    def test_policy_reaches_both_mcp_evidence_routes_and_audit(self):
        self.prepare()
        gateway = StdioGateway(self.manifest, self.state, interface="review")
        response = gateway.handle(self.request(1, "tools/call", {"name": "sentry_review_current_block", "arguments": {}}))["result"]["structuredContent"]
        self.assertEqual(response["privacy"]["approved_policy"], POLICY)
        self.assertEqual(response["privacy"]["enforcement"], "review_context_only")
        self.assertFalse(response["privacy"]["policy_changed"])
        paged = get_pending(self.manifest, self.state, response["review_id"])
        self.assertEqual(paged["privacy"], response["privacy"])
        self.assertIn("privacy", PENDING_OUTPUT_SCHEMA["required"])
        self.assertIn("privacy", CURRENT_REVIEW_OUTPUT_SCHEMA["required"])
        self.assertFalse(set(response) - set(CURRENT_REVIEW_OUTPUT_SCHEMA["properties"]))
        inspection = inspect(self.manifest, self.state)
        summary = Path(inspection["summary_report"]).read_text(encoding="utf-8")
        self.assertIn(response["privacy"]["approved_policy_hash"], summary)
        self.assertEqual(load_execution_envelope(self.state)["privacy_policy"], POLICY)

    def test_proposed_weaker_policy_does_not_replace_operator_policy(self):
        self.prepare()
        self.manifest_data["privacy_policy"]["rules"][0]["restricted_fields"] = []
        self.manifest_data["privacy_policy"]["rules"][0]["allowed_fields"].append("description")
        self.save_manifest()
        record, _ = ensure_pending(self.manifest, self.state)
        context = record["dossier"]["privacy"]
        self.assertEqual(context["approved_policy"], POLICY)
        self.assertTrue(context["policy_changed"])
        self.assertNotEqual(context["proposed_policy"], POLICY)
        # Even promoting only the code baseline cannot promote a weaker rule.
        accept_current(self.manifest, self.state)
        gateway = StdioGateway(self.manifest, self.state, interface="execution")
        self.addCleanup(gateway.backend.close)
        response = gateway.handle(self.request(2, "tools/call", {"name": "echo", "arguments": {"value": "x"}}))
        self.assertIn("promoção humana separada", json.dumps(response, ensure_ascii=False))
        self.assertEqual(gateway.backend.lifecycle.snapshot()["spawn_attempts"], 0)
        self.assertEqual(load_execution_envelope(self.state)["privacy_policy"], POLICY)

    def test_removed_policy_and_added_policy_need_separate_trust(self):
        self.prepare()
        del self.manifest_data["privacy_policy"]
        self.save_manifest()
        context = inspect(self.manifest, self.state)["dossier"]["privacy"]
        self.assertEqual(context["approved_policy"], POLICY)
        self.assertIsNone(context["proposed_policy"])
        self.assertTrue(context["policy_changed"])

    def test_existing_manifest_without_policy_remains_supported(self):
        approve(self.manifest, self.state)
        (self.project / "server.py").write_text(fixtures.SERVER_SOURCE + "\n# update\n", encoding="utf-8")
        context = inspect(self.manifest, self.state)["dossier"]["privacy"]
        self.assertEqual(context["status"], "not_configured")
        self.assertIsNone(context["approved_policy_hash"])
        self.manifest_data["privacy_policy"] = copy.deepcopy(POLICY)
        self.save_manifest()
        context = inspect(self.manifest, self.state)["dossier"]["privacy"]
        self.assertIsNone(context["approved_policy"])
        self.assertEqual(context["proposed_policy"], POLICY)
        self.assertTrue(context["policy_changed"])

    def test_operator_policy_promotion_invalidates_previous_evidence(self):
        self.prepare()
        original, _ = ensure_pending(self.manifest, self.state)
        self.manifest_data["privacy_policy"]["policy_id"] = "fixture-privacy-v2"
        self.save_manifest()
        proposed, _ = ensure_pending(self.manifest, self.state)
        self.assertNotEqual(original["review_id"], proposed["review_id"])
        with self.assertRaises(SentryError):
            promote_execution_envelope(self.manifest, self.state, "incorrect")
        promote_execution_envelope(self.manifest, self.state, "PROMOTE_EXECUTION_ENVELOPE")
        promoted, _ = ensure_pending(self.manifest, self.state)
        self.assertNotEqual(proposed["review_id"], promoted["review_id"])
        self.assertEqual(promoted["dossier"]["privacy"]["approved_policy"]["policy_id"], "fixture-privacy-v2")
        with self.assertRaises(SentryError):
            submit_verdict(self.manifest, self.state, self.verdict(proposed))

    def test_invalid_policy_rejected_before_any_backend_start(self):
        mutations = [
            lambda p: p.update(schema_version=True),
            lambda p: p.update(extra="unknown"),
            lambda p: p.update(rules=[]),
            lambda p: p["rules"][0].update(tools=["unknown_tool"]),
            lambda p: p["rules"].append(copy.deepcopy(p["rules"][0])),
            lambda p: p["rules"][0].update(restricted_fields=["value"]),
            lambda p: p["rules"][0].pop("output_scope"),
            lambda p: p["rules"][0].update(allowed_fields=["value", "value"]),
            lambda p: p["rules"][0].update(requirement=" "),
        ]
        for change in mutations:
            with self.subTest(change=mutations.index(change)):
                policy = copy.deepcopy(POLICY)
                change(policy)
                self.manifest_data["privacy_policy"] = policy
                self.save_manifest()
                with self.assertRaises(SentryError):
                    load(self.manifest)

    def test_old_review_policy_version_is_not_accepted(self):
        self.prepare()
        record, _ = ensure_pending(self.manifest, self.state)
        verdict = self.verdict(record)
        verdict["policy_version"] = "mcp-sentry-review-v1"
        with self.assertRaises(SentryError):
            submit_verdict(self.manifest, self.state, verdict)


if __name__ == "__main__":
    unittest.main()
