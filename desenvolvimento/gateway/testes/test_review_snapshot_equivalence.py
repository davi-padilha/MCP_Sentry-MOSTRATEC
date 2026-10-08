"""Equivalence of the review interface before and after optimization N1.

N1 reads the dossier from one inspection per sentry_review_current_block and
keeps only the fresh inspection made when an assessment is recorded. These
checks pin what the model receives and every acceptance or rejection of a
registration to the 1.0.0 behavior, reconstructed here from the public
review functions, which N1 does not change.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import test_gateway_universal as fixtures
from mcp_sentry_gateway import review
from mcp_sentry_gateway.core import approve
from mcp_sentry_gateway.gateway import StdioGateway
from mcp_sentry_gateway.review import get_pending, security_status

VOLATILE = {"review_token", "timings_ms", "telemetry_recorded"}


def reference_current_block(manifest, store):
    """The 1.0.0 sentry_review_current_block payload, without the token."""
    status = security_status(manifest, store)
    evidence = get_pending(manifest, store, status["review_id"], page=1, page_size=100)
    pages, page = [evidence], evidence["next_page"]
    while page is not None:
        item = get_pending(manifest, store, status["review_id"], page=page, page_size=100)
        pages.append(item)
        page = item["next_page"]
    evidence = {**evidence, "changes": [change for item in pages for change in item["changes"]], "has_more": False, "next_page": None}
    return {key: value for key, value in evidence.items() if key not in {"page", "page_size", "total_pages", "has_more", "next_page"}}


def stable(payload):
    return {key: value for key, value in payload.items() if key not in VOLATILE}


class ReviewSnapshotEquivalenceTests(unittest.TestCase):
    setUp = fixtures.UniversalGatewayTests.setUp
    save_manifest = fixtures.UniversalGatewayTests.save_manifest
    request = staticmethod(fixtures.UniversalGatewayTests.request)

    def change(self, marker="update", extra_files=0):
        (self.project / "server.py").write_bytes((fixtures.SERVER_SOURCE + f"\n# {marker}\n").encode())
        if extra_files:
            folder = self.project / "lib"
            folder.mkdir(exist_ok=True)
            for number in range(extra_files):
                (folder / f"m{number:03}.py").write_bytes(f"value = {number}  # {marker}\n".encode())

    def prepare(self, extra_files=0):
        if extra_files:
            folder = self.project / "lib"
            folder.mkdir()
            for number in range(extra_files):
                (folder / f"m{number:03}.py").write_bytes(f"value = {number}\n".encode())
            self.manifest_data["inspect_roots"].append("lib")
            self.save_manifest()
        approve(self.manifest, self.state)
        self.change(extra_files=extra_files)
        self.gateway = StdioGateway(self.manifest, self.state, interface="review")

    def call(self, name, arguments=None, gateway=None):
        return (gateway or self.gateway).handle(self.request(1, "tools/call", {"name": name, "arguments": arguments or {}}))["result"]

    def assessment(self, token, decision="block"):
        return {"review_token": token, "decision": decision, "justification": "fixture review", "risks": []}

    def persisted_verdicts(self):
        folder = self.state / "revisoes-de-atualizacoes"
        return {path.stem: json.loads(path.read_text(encoding="utf-8"))["verdict"] for path in folder.glob("*.json")}

    def inspections(self):
        folder = self.state / "relatorios-de-seguranca" / "performance"
        return sum(json.loads(path.read_text(encoding="utf-8"))["operation"] == "inspect" for path in folder.glob("*.json"))

    # What the model reads -------------------------------------------------------

    def test_dossier_equals_the_reference_for_one_change(self):
        self.prepare()
        payload = self.call("sentry_review_current_block")["structuredContent"]
        self.assertEqual(stable(payload), stable(reference_current_block(self.manifest, self.state)))
        self.assertIn("review_token", payload)

    def test_dossier_equals_the_reference_across_several_pages(self):
        self.prepare(extra_files=230)
        payload = self.call("sentry_review_current_block")["structuredContent"]
        self.assertEqual(payload["total_changes"], 231)
        self.assertEqual(len(payload["changes"]), 231)
        self.assertEqual(stable(payload), stable(reference_current_block(self.manifest, self.state)))
        self.assertIn("review_token", payload)

    def test_paginated_reading_still_requires_every_page_for_a_token(self):
        self.prepare(extra_files=3)
        status = self.call("sentry_security_status")["structuredContent"]
        page, seen = 1, []
        while page is not None:
            result = self.call("sentry_review_evidence", {"review_id": status["review_id"], "page": page, "page_size": 2})["structuredContent"]
            seen.append("review_token" in result)
            page = result["next_page"]
        self.assertEqual(seen, [False, True])
        self.assertNotIn("isError", self.call("sentry_record_assessment", self.assessment(result["review_token"])))

    # What can be recorded -----------------------------------------------------

    def test_token_registration_persists_exactly_the_read_binding(self):
        self.prepare()
        evidence = self.call("sentry_review_current_block")["structuredContent"]
        result = self.call("sentry_record_assessment", self.assessment(evidence["review_token"]))["structuredContent"]
        self.assertTrue(result["receipt"]["persisted"])
        for key, value in evidence["review_binding"].items():
            self.assertEqual(result["receipt"][key], value)
        self.assertEqual(self.persisted_verdicts()[evidence["review_id"]]["decision"], "block")

    def test_change_after_reading_rejects_registration_without_persisting(self):
        self.prepare()
        evidence = self.call("sentry_review_current_block")["structuredContent"]
        self.change("second update")
        result = self.call("sentry_record_assessment", self.assessment(evidence["review_token"], "allow"))
        self.assertEqual(result["structuredContent"]["code"], "REVIEW_ID_MISMATCH")
        self.assertTrue(all(verdict is None for verdict in self.persisted_verdicts().values()))

    def test_legacy_verdict_without_reading_is_incomplete_evidence(self):
        self.prepare()
        binding = reference_current_block(self.manifest, self.state)["review_binding"]
        verdict = {**binding, "decision": "allow", "justification": "fixture", "risks": []}
        result = self.call("sentry_record_assessment", {"verdict": verdict})["structuredContent"]
        self.assertEqual(result["code"], "EVIDENCE_INCOMPLETE")
        self.assertTrue(all(verdict is None for verdict in self.persisted_verdicts().values()))

    def test_legacy_verdict_errors_match_after_reading(self):
        self.prepare()
        evidence = self.call("sentry_review_current_block")["structuredContent"]
        cases = {
            "wrong reviewed hash": ({"reviewed_hash": "0" * 64}, "REVIEW_BINDING_MISMATCH"),
            "wrong dossier hash": ({"dossier_hash": "0" * 64}, "REVIEW_BINDING_MISMATCH"),
            "unknown review": ({"review_id": "review-000000000000000000000000"}, "REVIEW_ID_MISMATCH"),
            "wrong policy": ({"policy_version": "other"}, "POLICY_VERSION_MISMATCH"),
        }
        for name, (override, code) in cases.items():
            with self.subTest(case=name):
                verdict = {**evidence["review_binding"], "decision": "allow", "justification": "fixture", "risks": [], **override}
                self.assertEqual(self.call("sentry_record_assessment", {"verdict": verdict})["structuredContent"]["code"], code)
        self.assertTrue(all(verdict is None for verdict in self.persisted_verdicts().values()))

    def test_legacy_verdict_after_partial_reading_is_incomplete_evidence(self):
        self.prepare(extra_files=3)
        status = self.call("sentry_security_status")["structuredContent"]
        first = self.call("sentry_review_evidence", {"review_id": status["review_id"], "page": 1, "page_size": 2})["structuredContent"]
        self.assertTrue(first["has_more"])
        verdict = {**first["review_binding"], "decision": "allow", "justification": "fixture", "risks": []}
        result = self.call("sentry_record_assessment", {"verdict": verdict})["structuredContent"]
        self.assertEqual(result["code"], "EVIDENCE_INCOMPLETE")
        self.assertTrue(all(verdict is None for verdict in self.persisted_verdicts().values()))

    def test_reading_again_after_a_change_shows_the_new_version(self):
        self.prepare()
        first = self.call("sentry_review_current_block")["structuredContent"]
        self.change("second update")
        second = self.call("sentry_review_current_block")["structuredContent"]
        self.assertNotEqual(second["review_id"], first["review_id"])
        self.assertEqual(stable(second), stable(reference_current_block(self.manifest, self.state)))

    def test_token_from_another_connection_is_rejected(self):
        self.prepare()
        evidence = self.call("sentry_review_current_block")["structuredContent"]
        other = StdioGateway(self.manifest, self.state, interface="review")
        result = self.call("sentry_record_assessment", self.assessment(evidence["review_token"]), other)
        self.assertEqual(result["structuredContent"]["code"], "REVIEW_TOKEN_INVALID")

    def test_change_during_reading_never_yields_an_accepted_mixed_review(self):
        """A change between internal steps of one reading must not be recordable."""
        self.prepare()
        original = review.inspect
        calls = []
        def changing_inspect(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                self.change("changed while reading")
            return original(*args, **kwargs)
        with mock.patch.object(review, "inspect", changing_inspect):
            payload = self.call("sentry_review_current_block")
        if len(calls) < 2:
            self.change("changed while reading")  # a single-snapshot reading has no middle
        if payload.get("isError"):
            return  # 1.0.0 behavior: the reading itself fails.
        token = payload["structuredContent"]["review_token"]
        result = self.call("sentry_record_assessment", self.assessment(token, "allow"))
        self.assertEqual(result["structuredContent"]["code"], "REVIEW_ID_MISMATCH")
        self.assertTrue(all(verdict is None for verdict in self.persisted_verdicts().values()))

    # The optimization itself --------------------------------------------------

    def test_reading_and_recording_use_one_inspection_each(self):
        self.prepare(extra_files=230)
        before = self.inspections()
        evidence = self.call("sentry_review_current_block")["structuredContent"]
        self.assertEqual(self.inspections() - before, 1, "one snapshot per reading")
        before = self.inspections()
        self.call("sentry_record_assessment", self.assessment(evidence["review_token"]))
        self.assertEqual(self.inspections() - before, 1, "only the fresh check at registration")


if __name__ == "__main__":
    unittest.main()
