"""Equivalence checks for the verified copy, independent of how it is produced.

These properties must hold both for a fresh copy per connection (1.0.0) and
for any reuse of an earlier verified copy (optimization P4):

- the backend always runs exactly the approved bytes;
- nothing left in, planted in or changed in an earlier copy reaches execution,
  including files, links and state written by the backend itself;
- changed, one-time and newly accepted versions keep their current semantics;
- concurrent connections stay independent and copies do not accumulate.

With 1.0.0 no copy survives a connection, so the tampering steps find nothing
to change. A backend that writes into its own copy (state file, __pycache__)
makes a kept copy unusable, so the same checks also run against a quiet server
(QuietServerTests) whose copy is actually reused.
"""
import hashlib
import json
import os
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import test_gateway_universal as fixtures
from mcp_sentry_gateway.core import VERIFIED_COPIES_DIR, accept_current, approve
from mcp_sentry_gateway.gateway import StdioGateway
from mcp_sentry_gateway.operator import decide
from mcp_sentry_gateway.review import ensure_pending, submit_verdict


SERVER_TEMPLATE = '''WRITES_STATE = {writes}
import hashlib, json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
state_file = os.path.join(here, "backend-state.txt")
state_existed = os.path.exists(state_file)
if WRITES_STATE:
    with open(state_file, "w", encoding="utf-8") as stream:
        stream.write("written by the backend")
import helper
planted = []
for name in ("plugin", "linkedpkg"):
    try:
        __import__(name)
        planted.append(name)
    except ImportError:
        pass
with open(os.path.abspath(__file__), "rb") as stream:
    own_hash = hashlib.sha256(stream.read()).hexdigest()
ready = False
for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "copy-probe", "version": "1"}}
    elif method == "notifications/initialized":
        ready = True
        continue
    elif method == "tools/list" and ready:
        result = {"tools": [{"name": "whoami", "description": "Report the running code", "inputSchema": {"type": "object", "properties": {}}}]}
    elif method == "tools/call" and ready:
        report = {"server_sha256": own_hash, "helper": helper.VALUE, "planted": planted, "state_existed": state_existed}
        result = {"content": [{"type": "text", "text": json.dumps(report)}]}
    else:
        result = {"isError": True, "content": [{"type": "text", "text": "unsupported"}]}
    if "id" in request:
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}) + "\\n")
        sys.stdout.flush()
'''
HELPER_SOURCE = 'VALUE = "approved helper"\n'


def server_source(writes_state):
    return SERVER_TEMPLATE.replace("{writes}", str(writes_state))
TOOLS = [{"name": "whoami", "description": "Report the running code", "inputSchema": {"type": "object", "properties": {}}}]


class VerifiedCopyEquivalenceTests(unittest.TestCase):
    save_manifest = fixtures.UniversalGatewayTests.save_manifest
    request = staticmethod(fixtures.UniversalGatewayTests.request)
    WRITES_STATE = True

    @property
    def server_source(self):
        return server_source(self.WRITES_STATE)

    def setUp(self):
        fixtures.UniversalGatewayTests.setUp(self)
        (self.project / "server.py").write_bytes(self.server_source.encode("utf-8"))
        (self.project / "helper.py").write_bytes(HELPER_SOURCE.encode("utf-8"))
        self.manifest_data["inspect_roots"] = ["server.py", "helper.py"]
        self.manifest_data["metadata"]["tools"] = TOOLS
        self.save_manifest()
        self.outside = self.temp / "outside"
        self.outside.mkdir()

    # Helpers -----------------------------------------------------------------

    def open(self):
        gateway = StdioGateway(self.manifest, self.state, interface="execution")
        self.addCleanup(gateway.backend.close)
        return gateway

    def whoami(self, gateway):
        response = gateway.handle(self.request(1, "tools/call", {"name": "whoami", "arguments": {}}))
        result = response["result"]
        if result.get("structuredContent", {}).get("status"):
            return result["structuredContent"]
        return json.loads(result["content"][0]["text"])

    def run_once(self):
        gateway = self.open()
        try:
            return self.whoami(gateway), gateway.backend.lifecycle.snapshot()["spawn_attempts"]
        finally:
            gateway.backend.close()

    def approved_report(self, source=None):
        source = source or self.server_source
        return {"server_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                "helper": "approved helper", "planted": [], "state_existed": False}

    def kept_copies(self):
        folder = self.state / VERIFIED_COPIES_DIR
        return [path for path in folder.iterdir() if path.is_dir()] if folder.exists() else []

    def change_source(self, marker):
        source = self.server_source + f"\n# {marker}\n"
        (self.project / "server.py").write_bytes(source.encode("utf-8"))
        return source

    def allow_current(self):
        record, _ = ensure_pending(self.manifest, self.state)
        dossier = record["dossier"]
        submit_verdict(self.manifest, self.state, {
            "review_id": record["review_id"], "reviewed_hash": dossier["current_hash"],
            "dossier_hash": dossier["dossier_hash"], "policy_version": record["policy_version"],
            "decision": "allow", "justification": "fixture: expected local update", "risks": [],
        })

    # Approved bytes ------------------------------------------------------------

    def test_sequential_connections_run_the_approved_bytes(self):
        approve(self.manifest, self.state)
        for attempt in range(3):
            with self.subTest(attempt=attempt):
                report, spawns = self.run_once()
                self.assertEqual(report, self.approved_report())
                self.assertEqual(spawns, 1)

    def test_backend_state_from_an_earlier_connection_is_not_reused(self):
        approve(self.manifest, self.state)
        self.run_once()
        report, _ = self.run_once()
        self.assertFalse(report["state_existed"], "file written by an earlier backend reached a new connection")

    def test_tampered_kept_copy_never_executes(self):
        approve(self.manifest, self.state)
        self.run_once()
        for copy in self.kept_copies():
            for path in copy.rglob("server.py"):
                path.write_text(self.server_source.replace("approved", "tampered") + "\n# tampered\n", encoding="utf-8")
            for path in copy.rglob("helper.py"):
                path.write_text('VALUE = "tampered helper"\n', encoding="utf-8")
        report, _ = self.run_once()
        self.assertEqual(report, self.approved_report())

    def test_file_planted_in_kept_copy_is_not_loaded(self):
        approve(self.manifest, self.state)
        self.run_once()
        for copy in self.kept_copies():
            (copy / "plugin.py").write_text("RAN = True\n", encoding="utf-8")
        report, _ = self.run_once()
        self.assertEqual(report["planted"], [])

    def test_empty_directory_planted_in_kept_copy_is_not_imported(self):
        # An empty folder is importable as a Python namespace package.
        approve(self.manifest, self.state)
        self.run_once()
        for copy in self.kept_copies():
            (copy / "plugin").mkdir()
        report, _ = self.run_once()
        self.assertEqual(report["planted"], [])

    def test_link_planted_in_kept_copy_is_not_followed(self):
        target = self.outside / "linkedpkg"
        target.mkdir()
        (target / "__init__.py").write_text("RAN = True\n", encoding="utf-8")
        approve(self.manifest, self.state)
        self.run_once()
        for copy in self.kept_copies():
            link = copy / "linkedpkg"
            try:
                import _winapi
                _winapi.CreateJunction(str(target), str(link))
            except (ImportError, AttributeError, OSError):
                try:
                    link.symlink_to(target, target_is_directory=True)
                except (OSError, NotImplementedError) as exc:
                    self.skipTest(f"links unavailable: {exc}")
        report, _ = self.run_once()
        self.assertEqual(report["planted"], [])
        self.assertTrue((target / "__init__.py").is_file(), "removing a copy followed a planted link")

    # Version semantics -----------------------------------------------------------

    def test_changed_source_stays_blocked_after_a_successful_connection(self):
        approve(self.manifest, self.state)
        self.run_once()
        self.change_source("unreviewed update")
        report, spawns = self.run_once()
        self.assertEqual(report["status"], "security_review_required")
        self.assertEqual(spawns, 0)

    def test_accepted_version_replaces_the_previous_bytes(self):
        approve(self.manifest, self.state)
        self.run_once()
        source = self.change_source("accepted update")
        accept_current(self.manifest, self.state)
        report, _ = self.run_once()
        self.assertEqual(report, self.approved_report(source))

    def test_one_time_version_runs_once_and_baseline_still_runs_after(self):
        approve(self.manifest, self.state)
        self.run_once()
        source = self.change_source("one-time update")
        self.allow_current()
        decide(self.manifest, self.state, "once", input_fn=lambda: "AUTORIZAR", output=lambda _: None)
        report, _ = self.run_once()
        self.assertEqual(report, self.approved_report(source))
        blocked, spawns = self.run_once()
        self.assertEqual(spawns, 0)
        self.assertIn(blocked["status"], {"security_review_required", "security_blocked"})
        (self.project / "server.py").write_bytes(self.server_source.encode("utf-8"))
        report, _ = self.run_once()
        self.assertEqual(report, self.approved_report())

    # Concurrency and storage ------------------------------------------------------

    def test_concurrent_connections_are_independent(self):
        approve(self.manifest, self.state)
        first, second = self.open(), self.open()
        self.assertEqual(self.whoami(first), self.approved_report())
        self.assertEqual(self.whoami(second), self.approved_report())
        self.assertNotEqual(first.backend.copy_root, second.backend.copy_root)
        first.backend.close()
        report = self.whoami(second)
        self.assertEqual(report["server_sha256"], self.approved_report()["server_sha256"])
        self.assertEqual(report["helper"], "approved helper")

    def test_copies_do_not_accumulate(self):
        approve(self.manifest, self.state)
        for _ in range(4):
            self.run_once()
        self.assertLessEqual(len(self.kept_copies()), 1)

    def test_blocked_connection_creates_no_copy(self):
        approve(self.manifest, self.state)
        before = {path.name for path in self.kept_copies()}
        self.change_source("unreviewed update")
        self.run_once()
        self.assertEqual({path.name for path in self.kept_copies()}, before)


class QuietServerTests(VerifiedCopyEquivalenceTests):
    """Same checks with a backend that writes nothing, so its copy can be reused."""
    WRITES_STATE = False

    def setUp(self):
        super().setUp()
        self.manifest_data["configuration"]["command"] = ["python", "-B", "server.py"]
        self.save_manifest()

    def last_start(self):
        folder = self.state / "relatorios-de-seguranca" / "performance"
        starts = [json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("*.json")]
        starts = [event for event in starts if event["operation"] == "backend_start"]
        return max(starts, key=lambda event: event["created_at"])["timings_ms"]

    @unittest.skipUnless(os.name == "nt", "kept copies require Windows job containment")
    def test_unchanged_baseline_reuses_the_kept_copy(self):
        """The optimization itself: without this the checks above prove nothing new."""
        approve(self.manifest, self.state)
        self.run_once()
        first = self.kept_copies()
        self.assertEqual(len(first), 1)
        report, _ = self.run_once()
        self.assertEqual(report, self.approved_report())
        self.assertEqual(self.last_start().get("copy_reused"), 1)
        second = self.kept_copies()
        self.assertEqual(len(second), 1)
        self.assertNotEqual(second, first, "a reused copy moves to a new, unpredictable path")

    @unittest.skipUnless(os.name == "nt", "kept copies require Windows job containment")
    def test_legitimate_folder_swapped_for_identical_link_is_not_reused(self):
        """Same bytes behind a junction would leave the code editable outside the copy."""
        (self.project / "data").mkdir()
        (self.project / "data" / "config.txt").write_bytes(b"approved data\n")
        self.manifest_data["inspect_roots"].append("data")
        self.save_manifest()
        approve(self.manifest, self.state)
        self.run_once()
        copy = self.kept_copies()[0]
        twin = self.outside / "data"
        twin.mkdir()
        (twin / "config.txt").write_bytes(b"approved data\n")
        (copy / "data" / "config.txt").unlink()
        (copy / "data").rmdir()
        try:
            import _winapi
            _winapi.CreateJunction(str(twin), str(copy / "data"))
        except (ImportError, AttributeError, OSError):
            try:
                (copy / "data").symlink_to(twin, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"links unavailable: {exc}")
        report, _ = self.run_once()
        self.assertEqual(report, self.approved_report())
        self.assertEqual(self.last_start().get("copy_reused"), 0)
        self.assertTrue((twin / "config.txt").is_file(), "removing a copy followed a planted link")

    @unittest.skipUnless(os.name == "nt", "kept copies require Windows job containment")
    def test_tampered_copy_is_replaced_not_reused(self):
        approve(self.manifest, self.state)
        self.run_once()
        (self.kept_copies()[0] / "plugin.py").write_text("RAN = True\n", encoding="utf-8")
        self.run_once()
        self.assertEqual(self.last_start().get("copy_reused"), 0)
        self.assertFalse((self.kept_copies()[0] / "plugin.py").exists())


if __name__ == "__main__":
    unittest.main()
