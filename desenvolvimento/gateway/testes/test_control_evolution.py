"""Binding, durable receipts, declared privacy and advisory stage measurements."""
import copy
import json
import unittest
from unittest import mock

import test_gateway_universal as fixtures
from mcp_sentry_gateway.core import approve, inspect
from mcp_sentry_gateway.gateway import StdioGateway
from mcp_sentry_gateway.privacy import privacy_context


class ControlEvolutionTests(unittest.TestCase):
    setUp = fixtures.UniversalGatewayTests.setUp
    save_manifest = fixtures.UniversalGatewayTests.save_manifest
    request = staticmethod(fixtures.UniversalGatewayTests.request)

    def prepare(self):
        approve(self.manifest, self.state)
        (self.project / "server.py").write_text(fixtures.SERVER_SOURCE + "\n# controlled update\n", encoding="utf-8")
        self.gateway = StdioGateway(self.manifest, self.state, interface="review")
        return self.call("sentry_review_current_block", {})["structuredContent"]

    def call(self, name, arguments):
        return self.gateway.handle(self.request(1, "tools/call", {"name": name, "arguments": arguments}))["result"]

    def verdict(self, evidence, **changes):
        return {**evidence["review_binding"], "decision": "block", "justification": 'password="FAKE_SECRET"',
                "risks": ['token="FAKE_TOKEN"'], **changes}

    def test_binding_and_receipt_match_durable_sanitized_record(self):
        evidence = self.prepare()
        self.assertEqual(evidence["review_binding"]["reviewed_hash"], evidence["current_hash"])
        result = self.call("sentry_record_assessment", {"verdict": self.verdict(evidence)})
        self.assertNotIn("isError", result)
        receipt = result["structuredContent"]["receipt"]
        record = json.loads((self.state / "revisoes-de-atualizacoes" / (receipt["review_id"] + ".json")).read_text())
        self.assertEqual(receipt["justification"], record["verdict"]["justification"])
        self.assertEqual(receipt["risks"], record["verdict"]["risks"])
        self.assertNotIn("FAKE_SECRET", json.dumps(result))
        self.assertNotIn("FAKE_TOKEN", json.dumps(result))
        self.assertFalse(receipt["execution_authorized"])
        self.assertTrue(receipt["persisted"])
        self.assertIsNone(self.gateway.backend)

    def test_invalid_identity_and_hash_are_rejected_without_repair(self):
        evidence = self.prepare()
        for change, code in (({"review_id": "invented"}, "REVIEW_ID_MISMATCH"),
                             ({"dossier_hash": "0" * 64}, "REVIEW_BINDING_MISMATCH")):
            result = self.call("sentry_record_assessment", {"verdict": self.verdict(evidence, **change)})
            self.assertTrue(result["isError"])
            self.assertEqual(result["structuredContent"]["code"], code)
            self.assertEqual(result["structuredContent"]["recovery_tool"], "sentry_review_current_block")
        record = json.loads((self.state / "revisoes-de-atualizacoes" / (evidence["review_id"] + ".json")).read_text())
        self.assertIsNone(record["verdict"])
        self.assertIsNone(self.gateway.backend)

    def test_measurements_do_not_change_dossier_identity(self):
        self.prepare()
        first = inspect(self.manifest, self.state)
        second = inspect(self.manifest, self.state)
        self.assertEqual(first["dossier"], second["dossier"])
        self.assertNotIn("timings_ms", first["dossier"])
        self.assertTrue(all(value >= 0 for value in first["timings_ms"].values()))
        events = list((self.state / "relatorios-de-seguranca" / "performance").glob("*.json"))
        self.assertTrue(events)
        self.assertNotIn(str(self.project), events[0].read_text())

    def test_advisory_telemetry_failure_does_not_undo_persisted_block(self):
        evidence = self.prepare()
        with mock.patch("mcp_sentry_gateway.telemetry.record_timings", return_value=False):
            result = self.call("sentry_record_assessment", {"verdict": self.verdict(evidence)})["structuredContent"]
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["receipt"]["persisted"])
        self.assertFalse(result["telemetry_recorded"])

    def test_declared_contract_neither_infers_permissions_nor_trusts_proposed_policy(self):
        approved = {"schema_version": 1, "policy_id": "allowed", "rules": [{"rule_id": "scope", "tools": ["echo"], "requirement": "Only requested data"}]}
        proposed = copy.deepcopy(approved)
        proposed["rules"][0]["requirement"] = "Any data"
        contract = privacy_context({"privacy_policy": approved}, {"privacy_policy": proposed})["reference_contract"]
        self.assertEqual(contract["rules"][0]["requirement"], "Only requested data")
        self.assertNotIn("allowed_fields", contract["rules"][0])
        self.assertEqual(contract["compliance"], "not_certified")
        self.assertFalse(contract["observed_output_verified"])
        self.assertEqual(privacy_context({}, {})["reference_contract"]["status"], "not_declared")


if __name__ == "__main__":
    unittest.main()
