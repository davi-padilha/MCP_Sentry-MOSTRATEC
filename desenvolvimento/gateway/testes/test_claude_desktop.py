"""Claude Desktop installation boundaries using disposable files and real stdio."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import test_setup
from mcp_sentry_gateway import claude_desktop as claude
from mcp_sentry_gateway.administration import inventory
from mcp_sentry_gateway.core import SentryError, digest
from mcp_sentry_gateway.gateway import StdioGateway
from mcp_sentry_gateway.setup import run_setup


class ClaudeDesktopTests(unittest.TestCase):
    def setUp(self):
        test_setup.SetupTests.setUp(self)
        self.config = self.temp / "claude_desktop_config.json"
        self.data = {"preferences": {"keep": True}, "mcpServers": {
            "example": {"command": sys.executable, "args": [str(self.script)],
                        "env": {"SERVER_GREETING": "secret-test-value"}},
            "other": {"command": "other-executable", "args": ["keep"]}}}
        self.save()
        self.original = self.config.read_bytes()

    def save(self):
        self.config.write_text(json.dumps(self.data), encoding="utf-8")

    def run_answers(self, *answers, output=None):
        values = iter(answers)
        messages = []
        result = run_setup(self.config, self.state_root, requested_name="example", client="claude-desktop",
                           input_fn=values.__next__, output=output or messages.append)
        return result, "\n".join(messages)

    def install(self):
        return self.run_answers("", "", "DESCOBRIR", "APROVAR", "SUBSTITUIR")[0]

    def test_setup_preserves_other_options_and_separates_credentials(self):
        result, messages = self.run_answers("", "", "DESCOBRIR", "APROVAR", "SUBSTITUIR")
        self.assertEqual(result["status"], "connected_restart_required")
        self.assertEqual(Path(result["backup"]).read_bytes(), self.original)
        configured = claude.configuration(self.config)[1]
        self.assertEqual(configured["preferences"], self.data["preferences"])
        self.assertEqual(configured["mcpServers"]["other"], self.data["mcpServers"]["other"])
        self.assertEqual(configured["mcpServers"]["example"]["env"], self.data["mcpServers"]["example"]["env"])
        self.assertNotIn("env", configured["mcpServers"]["mcp_sentry_review_example"])
        self.assertNotIn("env_vars", configured["mcpServers"]["example"])
        self.assertNotIn("secret-test-value", messages)
        receipt = Path(result["installation_record"])
        self.assertEqual(receipt.name, "claude-desktop-installation.json")
        self.assertNotIn("secret-test-value", receipt.read_text(encoding="utf-8"))
        self.assertTrue((receipt.parent / "config/claude-desktop-fragment.json").is_file())
        manifest, store = Path(result["manifest"]), receipt.parent / "state"
        self.assertEqual(claude.doctor(manifest, store, self.config, "example")["status"], "ready")
        gateway = StdioGateway(manifest, store, interface="execution")
        self.addCleanup(gateway.backend.close)
        with mock.patch.dict(os.environ, {"SERVER_GREETING": "native-"}):
            response = gateway.handle({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "echo", "arguments": {"value": "ok"}}})
        self.assertEqual(response["result"]["content"][0]["text"], "native-ok")
        gateway.backend.close()
        self.script.write_text(test_setup.SERVER_SOURCE + "\n# changed\n", encoding="utf-8")
        blocked = StdioGateway(manifest, store, interface="execution")
        self.addCleanup(blocked.backend.close)
        response = blocked.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                   "params": {"name": "echo", "arguments": {"value": "ok"}}})
        self.assertEqual(response["result"]["structuredContent"]["status"], "security_review_required")
        self.assertEqual(blocked.backend.lifecycle.snapshot()["spawn_attempts"], 0)

    def test_cancellations_preserve_client_and_approval_boundary(self):
        for stage, answers, expected, approved in (
            ("discovery", ("", "", "no"), "cancelled_before_discovery", False),
            ("approval", ("", "", "DESCOBRIR", "no"), "prepared_not_approved", False),
            ("connection", ("", "", "DESCOBRIR", "APROVAR", "no"), "approved_not_connected", True),
        ):
            with self.subTest(stage=stage):
                self.state_root = self.temp / stage
                result, _ = self.run_answers(*answers)
                self.assertEqual(result["status"], expected)
                self.assertEqual(self.config.read_bytes(), self.original)
                self.assertEqual((self.state_root / "example/state/versao-aprovada.json").is_file(), approved)

    def test_selective_restore_keeps_other_edits_and_is_idempotent(self):
        result = self.install()
        record = Path(result["installation_record"])
        current = claude.configuration(self.config)[1]
        current["preferences"]["later"] = "keep"
        current["mcpServers"]["new"] = {"command": "new"}
        self.config.write_text(json.dumps(current), encoding="utf-8")
        before = self.config.read_bytes()
        self.assertEqual(claude.restore(record)["status"], "restore_preview")
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(claude.restore(record, apply=True)["status"], "restored_restart_required")
        restored = claude.configuration(self.config)[1]
        self.assertEqual(restored["mcpServers"]["example"], self.data["mcpServers"]["example"])
        self.assertNotIn("mcp_sentry_review_example", restored["mcpServers"])
        self.assertEqual(restored["preferences"]["later"], "keep")
        self.assertIn("new", restored["mcpServers"])
        self.assertEqual(claude.restore(record, apply=True)["status"], "already_restored")
        self.assertTrue((record.parent / "state/versao-aprovada.json").exists())

    def test_restore_rejects_changed_managed_entry_and_changed_backup(self):
        result = self.install()
        record = Path(result["installation_record"])
        installed = self.config.read_bytes()
        changed = claude.parse(installed)
        changed["mcpServers"]["example"]["env"]["SERVER_GREETING"] = "user-edit"
        self.config.write_text(json.dumps(changed), encoding="utf-8")
        before = self.config.read_bytes()
        with self.assertRaisesRegex(SentryError, "conflito"):
            claude.restore(record, apply=True)
        self.assertEqual(self.config.read_bytes(), before)
        self.config.write_bytes(installed)
        Path(result["backup"]).write_bytes(b"changed")
        with self.assertRaisesRegex(SentryError, "backup mudou"):
            claude.restore(record, apply=True)
        self.assertEqual(self.config.read_bytes(), installed)

    def test_concurrent_edit_is_preserved_during_connection(self):
        def output(message):
            if message.startswith("Digite SUBSTITUIR"):
                self.data["preferences"]["concurrent"] = True
                self.save()
        with self.assertRaisesRegex(SentryError, "mudou durante a preparação"):
            self.run_answers("", "", "DESCOBRIR", "APROVAR", "SUBSTITUIR", output=output)
        self.assertTrue(claude.configuration(self.config)[1]["preferences"]["concurrent"])

    def test_diagnostic_failure_rolls_back_client(self):
        with mock.patch.object(claude, "doctor", return_value={"status": "needs_attention", "issues": ["fixture"]}):
            with self.assertRaisesRegex(SentryError, "original restaurada"):
                self.install()
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_record_write_failure_rolls_back_client(self):
        with mock.patch.object(claude, "installation_record", side_effect=OSError("fixture")):
            with self.assertRaisesRegex(SentryError, "original restaurada"):
                self.install()
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_unsupported_fields_and_review_collision_fail_before_discovery(self):
        for field in ("cwd", "unknown"):
            with self.subTest(field=field):
                self.data["mcpServers"]["example"][field] = "value"
                self.save()
                with mock.patch("mcp_sentry_gateway.setup.prepare_codex") as prepare:
                    with self.assertRaisesRegex(SentryError, "não migradas"):
                        self.run_answers()
                    prepare.assert_not_called()
                self.data["mcpServers"]["example"].pop(field)
        self.data["mcpServers"]["mcp_sentry_review_example"] = {"command": "keep"}
        self.save()
        with self.assertRaisesRegex(SentryError, "já existe uma entrada de revisão"):
            self.run_answers()
        self.assertFalse(self.state_root.exists())

    def test_bom_and_crlf_supported_and_preserved(self):
        self.config.write_bytes(b"\xef\xbb\xbf" + json.dumps(self.data, indent=2).replace("\n", "\r\n").encode())
        self.original = self.config.read_bytes()
        self.install()
        self.assertTrue(self.config.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"\r\n", self.config.read_bytes())

    def test_invalid_json_and_duplicate_keys_do_not_disclose_source(self):
        for raw in (b'{"mcpServers":{},"secret":"private", BAD}', b'{"mcpServers":{},"mcpServers":{}}', b'{"mcpServers":{},"x":NaN}'):
            with self.subTest(raw=raw):
                self.config.write_bytes(raw)
                with self.assertRaises(SentryError) as caught:
                    self.run_answers()
                self.assertNotIn("private", str(caught.exception))
                self.assertEqual(self.config.read_bytes(), raw)

    def test_doctor_catches_missing_pair_wrong_binding_and_review_environment(self):
        result = self.install()
        manifest, store = Path(result["manifest"]), Path(result["installation_record"]).parent / "state"
        current = claude.configuration(self.config)[1]
        current["mcpServers"]["example"]["args"][-1] = "wrong-store"
        current["mcpServers"]["mcp_sentry_review_example"]["env"] = {"SECRET": "private"}
        self.config.write_text(json.dumps(current), encoding="utf-8")
        result = claude.doctor(manifest, store, self.config, "example")
        self.assertEqual(result["status"], "needs_attention")
        self.assertIn("example.args difere", " ".join(result["issues"]))
        self.assertIn("revisão não deve receber", " ".join(result["issues"]))
        self.assertNotIn("private", json.dumps(result))

    def test_inventory_is_read_only(self):
        result = self.install()
        state = Path(result["installation_record"]).parent / "state"
        before = {p.relative_to(state): digest(p.read_bytes()) for p in state.rglob("*") if p.is_file()}
        first = inventory(self.config, "claude-desktop")
        self.assertEqual(first["servers"][0]["status"], "unchanged")
        self.script.write_text(test_setup.SERVER_SOURCE + "\n# changed\n", encoding="utf-8")
        second = inventory(self.config, "claude-desktop")
        self.assertEqual(second["servers"][0]["status"], "review_required")
        self.assertEqual(before, {p.relative_to(state): digest(p.read_bytes()) for p in state.rglob("*") if p.is_file()})

    def test_chat_approval_option_is_configured_and_diagnosed_in_both_interfaces(self):
        answers = iter(("", "", "DESCOBRIR", "APROVAR", "SUBSTITUIR"))
        result = run_setup(self.config, self.state_root, requested_name="example", client="claude-desktop",
                           conversation_approval=True, input_fn=answers.__next__, output=lambda _: None)
        entries = claude.configuration(self.config)[2]
        for name in ("example", "mcp_sentry_review_example"):
            self.assertIn("--conversation-approval", entries[name]["args"])
        manifest = Path(result["manifest"])
        store = Path(result["installation_record"]).parent / "state"
        self.assertEqual(claude.doctor(manifest, store, self.config, "example")["status"], "ready")
        entries["mcp_sentry_review_example"]["args"].remove("--conversation-approval")
        data = claude.configuration(self.config)[1]
        data["mcpServers"] = entries
        self.config.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(claude.doctor(manifest, store, self.config, "example")["status"], "needs_attention")

    def test_detection_standard_store_ambiguity_and_missing(self):
        appdata, local = self.temp / "roaming", self.temp / "local"
        standard = appdata / "Claude/claude_desktop_config.json"
        store = local / "Packages/Claude_example/LocalCache/Roaming/Claude/claude_desktop_config.json"
        with mock.patch.dict(os.environ, {"APPDATA": str(appdata), "LOCALAPPDATA": str(local)}):
            with self.assertRaisesRegex(SentryError, "não encontrada"):
                claude.default_config()
            standard.parent.mkdir(parents=True)
            standard.write_bytes(self.original)
            self.assertEqual(claude.default_config(), standard.resolve())
            store.parent.mkdir(parents=True)
            store.write_bytes(self.original)
            with self.assertRaisesRegex(SentryError, "mais de uma"):
                claude.default_config()
            standard.unlink()
            self.assertEqual(claude.default_config(), store.resolve())

    def test_already_protected_and_remote_entries_are_not_candidates(self):
        self.assertFalse(claude.eligible("example", {"url": "https://example.invalid"}))
        self.assertFalse(claude.eligible("example", {"command": "python", "type": "http"}))
        self.assertFalse(claude.eligible("example", {"command": sys.executable, "args": ["-m", "mcp_sentry_gateway.gateway"]}))
        self.assertFalse(claude.eligible("mcp_sentry_review_example", {"command": sys.executable}))
        self.assertFalse(claude.eligible("../escape", {"command": sys.executable}))


if __name__ == "__main__":
    unittest.main()
