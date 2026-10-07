"""Security boundaries for token registration, inventory, restoration and startup timings."""
import json
import sys
import tomllib
import unittest
from unittest import mock

import test_gateway_universal as fixtures
import test_setup
from mcp_sentry_gateway.administration import inventory, restore_codex
from mcp_sentry_gateway.core import SentryError, approve
from mcp_sentry_gateway.gateway import StdioGateway


class RegistrationTests(unittest.TestCase):
    setUp = fixtures.UniversalGatewayTests.setUp
    save_manifest = fixtures.UniversalGatewayTests.save_manifest
    request = staticmethod(fixtures.UniversalGatewayTests.request)

    def prepare(self):
        approve(self.manifest, self.state)
        (self.project/"server.py").write_text(fixtures.SERVER_SOURCE+"\n# first update\n")
        self.gateway = StdioGateway(self.manifest, self.state, interface="review")
        return self.call("sentry_review_current_block", {})["structuredContent"]

    def call(self, name, arguments, gateway=None):
        return (gateway or self.gateway).handle(self.request(1, "tools/call", {"name": name, "arguments": arguments}))["result"]

    def args(self, token):
        return {"review_token": token, "decision": "block", "justification": "controlled evidence", "risks": []}

    def test_token_records_exact_read_binding_and_cannot_be_replayed(self):
        evidence = self.prepare()
        result = self.call("sentry_record_assessment", self.args(evidence["review_token"]))
        self.assertNotIn("isError", result)
        receipt = result["structuredContent"]["receipt"]
        for key, value in evidence["review_binding"].items():
            self.assertEqual(receipt[key], value)
        self.assertFalse(receipt["execution_authorized"])
        self.assertTrue(self.call("sentry_record_assessment", self.args(evidence["review_token"]))["isError"])
        self.assertIsNone(self.gateway.backend)

    def test_forged_other_connection_and_stale_tokens_fail(self):
        evidence = self.prepare()
        other = StdioGateway(self.manifest, self.state, interface="review")
        for gateway, token in ((self.gateway, "invented"), (other, evidence["review_token"])):
            result = self.call("sentry_record_assessment", self.args(token), gateway)
            self.assertEqual(result["structuredContent"]["code"], "REVIEW_TOKEN_INVALID")
            self.assertIn("Releia", result["structuredContent"]["recovery_instruction"])
        (self.project/"server.py").write_text(fixtures.SERVER_SOURCE+"\n# a different update\n")
        result = self.call("sentry_record_assessment", self.args(evidence["review_token"]))
        self.assertEqual(result["structuredContent"]["code"], "REVIEW_ID_MISMATCH")
        current = self.call("sentry_review_current_block", {})["structuredContent"]
        self.assertNotEqual(current["review_token"], evidence["review_token"])
        self.assertNotIn("isError", self.call("sentry_record_assessment", self.args(current["review_token"])))

    def test_expired_token_does_not_bind_replacement_generation(self):
        evidence = self.prepare()
        p=self.state/"revisoes-de-atualizacoes"/(evidence["review_id"]+".json")
        record=json.loads(p.read_text());record["created_at"]="2000-01-01T00:00:00+00:00";p.write_text(json.dumps(record))
        self.assertTrue(self.call("sentry_record_assessment", self.args(evidence["review_token"]))["isError"])
        self.assertNotEqual(self.call("sentry_review_current_block", {})["structuredContent"]["review_id"],evidence["review_id"])

    def test_formats_cannot_be_mixed_and_legacy_hashes_still_fail(self):
        evidence = self.prepare()
        legacy = {**evidence["review_binding"], "decision": "block", "justification": "fixture", "risks": []}
        mixed = {**self.args(evidence["review_token"]), "verdict": legacy}
        self.assertTrue(self.call("sentry_record_assessment", mixed)["isError"])
        legacy["reviewed_hash"] = "0"*64
        self.assertEqual(self.call("sentry_record_assessment", {"verdict":legacy})["structuredContent"]["code"],"REVIEW_BINDING_MISMATCH")

    def test_partial_evidence_has_no_token(self):
        evidence=self.prepare()
        other=StdioGateway(self.manifest,self.state,interface="review")
        # Add a second changed artifact and use the paginated path in a fresh session.
        self.manifest_data["inspect_roots"].append("second.py");self.save_manifest()
        (self.project/"second.py").write_text("value = 1\n")
        status=self.call("sentry_security_status",{},other)["structuredContent"]
        first=self.call("sentry_review_evidence",{"review_id":status["review_id"],"page_size":1},other)["structuredContent"]
        self.assertTrue(first["has_more"]);self.assertNotIn("review_token",first)
        page=first["next_page"]
        while page is not None:
            result=self.call("sentry_review_evidence",{"review_id":status["review_id"],"page":page,"page_size":1},other)["structuredContent"]
            page=result["next_page"]
        self.assertIn("review_token",result)

    def test_successful_startup_timings_do_not_change_native_response(self):
        approve(self.manifest,self.state)
        gateway=StdioGateway(self.manifest,self.state,interface="execution")
        self.addCleanup(gateway.backend.close)
        result=self.call("echo",{"value":"native value"},gateway)
        self.assertEqual(result,{"content":[{"type":"text","text":"native value"}]})
        events=[json.loads(p.read_text()) for p in (self.state/"relatorios-de-seguranca/performance").glob("*.json")]
        timings=next(x["timings_ms"] for x in events if x["operation"]=="backend_start")
        self.assertEqual(set(timings),{"pre_spawn_check","source_capture","verified_copy","spawn","backend_initialize","catalog_check","startup_total"})
        self.assertTrue(all(x>=0 for x in timings.values()))
        self.assertGreaterEqual(timings["startup_total"],sum(v for k,v in timings.items() if k!="startup_total"))


class AdministrationTests(unittest.TestCase):
    setUp=test_setup.SetupTests.setUp
    run_answers=test_setup.SetupTests.run_answers

    def install(self):
        result,_=self.run_answers("","","DESCOBRIR","APROVAR","SUBSTITUIR")
        from pathlib import Path
        return Path(result["installation_record"])

    def test_restore_preview_apply_preserves_unrelated_edits_and_is_idempotent(self):
        record=self.install()
        self.config.write_text(self.config.read_text().replace('model = "some-model"','model = "later-model"').replace('https://example.invalid/mcp','https://changed.invalid/mcp'))
        before=self.config.read_bytes()
        self.assertEqual(restore_codex(record)["status"],"restore_preview")
        self.assertEqual(self.config.read_bytes(),before)
        result=restore_codex(record,apply=True)
        self.assertEqual(result["status"],"restored_restart_required")
        data=tomllib.loads(self.config.read_text());old=tomllib.loads(self.original.decode())
        self.assertEqual(data["mcp_servers"]["example"],old["mcp_servers"]["example"])
        self.assertNotIn("mcp_sentry_review_example",data["mcp_servers"])
        self.assertEqual(data["model"],"later-model")
        self.assertEqual(data["mcp_servers"]["remote"]["url"],"https://changed.invalid/mcp")
        self.assertEqual(restore_codex(record,apply=True)["status"],"already_restored")
        self.assertTrue((self.state_root/"example/state/versao-aprovada.json").exists())

    def test_conflicting_server_edit_aborts_without_partial_restoration(self):
        record=self.install()
        text=self.config.read_text().replace('startup_timeout_sec = 60.0','startup_timeout_sec = 61.0')
        self.config.write_text(text);before=self.config.read_bytes()
        with self.assertRaisesRegex(SentryError,"conflito"):
            restore_codex(record,apply=True)
        self.assertEqual(self.config.read_bytes(),before)

    def test_modified_backup_is_rejected(self):
        record=self.install();info=json.loads(record.read_text())
        from pathlib import Path
        Path(info["backup"]).write_bytes(b'model="changed"\n')
        before=self.config.read_bytes()
        with self.assertRaisesRegex(SentryError,"backup mudou"):
            restore_codex(record,apply=True)
        self.assertEqual(self.config.read_bytes(),before)

    def test_comment_edit_in_managed_table_is_preserved_as_conflict(self):
        record=self.install()
        text=self.config.read_text()
        header='[mcp_servers."example"]'
        self.assertIn(header,text)
        self.config.write_text(text.replace(header, header+'\n# user note after setup'))
        before=self.config.read_bytes()
        with self.assertRaisesRegex(SentryError,"conflito no texto"):
            restore_codex(record,apply=True)
        self.assertEqual(self.config.read_bytes(),before)

    def test_inventory_is_read_only_and_distinguishes_pending_and_human_wait(self):
        self.install();folder=self.state_root/"example"
        snapshot=lambda:{str(p.relative_to(folder)):p.read_bytes() for p in folder.rglob("*") if p.is_file()}
        before=snapshot();data=inventory(self.config)
        self.assertEqual(len(data["servers"]),1)
        self.assertEqual(data["servers"][0]["status"],"unchanged")
        self.assertEqual(snapshot(),before)
        self.script.write_text(fixtures.SERVER_SOURCE+"\n# update\n")
        self.assertEqual(inventory(self.config)["servers"][0]["status"],"review_required")
        manifest=folder/"configuration/manifest.json"
        # Setup writes its manifest path in the actual execution entry.
        args=tomllib.loads(self.config.read_text())["mcp_servers"]["example"]["args"]
        from pathlib import Path
        manifest=Path(args[args.index("--manifest")+1]);state=Path(args[args.index("--store")+1])
        gateway=StdioGateway(manifest,state,interface="review")
        call=lambda name,args:gateway.handle(fixtures.UniversalGatewayTests.request(1,"tools/call",{"name":name,"arguments":args}))["result"]["structuredContent"]
        e=call("sentry_review_current_block",{})
        call("sentry_record_assessment",{"review_token":e["review_token"],"decision":"allow","justification":"controlled fixture","risks":[]})
        before=snapshot();data=inventory(self.config)["servers"][0]
        self.assertTrue(data["awaiting_human_decision"])
        self.assertEqual(data["last_assessment"]["decision"],"allow")
        self.assertEqual(snapshot(),before)


if __name__=="__main__":
    unittest.main()
