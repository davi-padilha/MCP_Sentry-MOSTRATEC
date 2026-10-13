"""Permanent acceptance: exact user scope, atomic evidence and repeated use."""
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

import test_gateway_universal as fixtures
from mcp_sentry_gateway import core
from mcp_sentry_gateway.gateway import StdioGateway
from mcp_sentry_gateway.review import CONVERSATION_ACCEPT_CONFIRMATION, CONVERSATION_CONFIRMATION, submit_verdict


class PermanentApprovalTests(unittest.TestCase):
    setUp = fixtures.UniversalGatewayTests.setUp
    save_manifest = fixtures.UniversalGatewayTests.save_manifest
    request = staticmethod(fixtures.UniversalGatewayTests.request)

    def tool(self, gateway, name, arguments=None):
        return gateway.handle(self.request(1, 'tools/call', {'name': name, 'arguments': arguments or {}}))['result']

    def prepare(self, source=None):
        core.approve(self.manifest, self.state)
        self.before = (self.state/'versao-aprovada.json').read_bytes()
        self.envelope = (self.state/'configuracao-de-execucao-aprovada.json').read_bytes()
        (self.project/'server.py').write_text(source or fixtures.SERVER_SOURCE+'\n# benign update\n', encoding='utf-8')
        self.review = StdioGateway(self.manifest, self.state, interface='review', conversation_approval=True)
        self.execution = StdioGateway(self.manifest, self.state, interface='execution', conversation_approval=True)
        self.addCleanup(lambda: self.execution.backend.close())
        self.read()

    def read(self):
        self.evidence = self.tool(self.review, 'sentry_review_current_block')['structuredContent']
        self.accept_args = {key: self.evidence['review_binding'][key] for key in ('review_id', 'reviewed_hash', 'dossier_hash')}
        self.accept_args['confirmation'] = CONVERSATION_ACCEPT_CONFIRMATION

    def record(self, decision='allow'):
        return self.tool(self.review, 'sentry_record_assessment', {
            'review_token': self.evidence['review_token'], 'decision': decision,
            'justification': 'Controlled fixture; not a model assessment.', 'risks': []})

    def accept(self, args=None, gateway=None):
        return self.tool(gateway or self.review, 'sentry_accept_version', self.accept_args if args is None else args)

    def echo(self, value='ok', gateway=None):
        return self.tool(gateway or self.execution, 'echo', {'value': value})

    def assert_unchanged(self):
        self.assertEqual((self.state/'versao-aprovada.json').read_bytes(), self.before)
        self.assertEqual((self.state/'configuracao-de-execucao-aprovada.json').read_bytes(), self.envelope)
        self.assertEqual(self.execution.backend.lifecycle.snapshot()['spawn_attempts'], 0)

    def test_permanent_acceptance_allows_repeated_calls_and_reconnection(self):
        self.prepare()
        options = self.record()['structuredContent']['approval_options']
        self.assertEqual({item['scope'] for item in options}, {'one_call', 'accepted_version'})
        self.assertEqual(self.echo()['structuredContent']['status'], 'security_blocked')
        accepted = self.accept()['structuredContent']
        self.assertEqual(accepted['status'], 'version_accepted')
        self.assertFalse(accepted['backend_started'])
        self.assertEqual(self.execution.backend.lifecycle.snapshot()['spawn_attempts'], 0)
        self.assertEqual((self.state/'configuracao-de-execucao-aprovada.json').read_bytes(), self.envelope)
        for value in ('first', 'second'):
            self.assertEqual(self.echo(value)['content'][0]['text'], value)
        self.execution.backend.close()
        fresh = StdioGateway(self.manifest, self.state, interface='execution')
        self.addCleanup(fresh.backend.close)
        self.assertEqual(self.echo('reconnected', fresh)['content'][0]['text'], 'reconnected')
        status = self.tool(self.review, 'sentry_security_status')['structuredContent']
        self.assertEqual(status['authorization_state'], 'version_accepted')
        self.assertEqual(status['authorization_scope'], 'accepted_version')
        (self.project/'server.py').write_text(fixtures.SERVER_SOURCE+'\n# next update\n', encoding='utf-8')
        blocked = self.echo('must not run', fresh)
        self.assertEqual(blocked['structuredContent']['status'], 'security_review_required')

    def test_opt_in_only_and_execution_interface_cannot_accept(self):
        self.prepare()
        self.record()
        default = StdioGateway(self.manifest, self.state, interface='review')
        self.assertTrue(self.accept(gateway=default)['isError'])
        catalog = default.handle(self.request(2, 'tools/list'))['result']['tools']
        self.assertNotIn('sentry_accept_version', {tool['name'] for tool in catalog})
        response = self.execution.handle(self.request(2, 'tools/call', {'name': 'sentry_accept_version', 'arguments': self.accept_args}))
        self.assertIn('error', response)
        self.assert_unchanged()

    def test_missing_blocked_and_nonclient_assessment_cannot_accept(self):
        self.prepare()
        self.assertTrue(self.accept()['isError'])
        self.record('block')
        self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_local_fixture_assessment_is_not_client_consent(self):
        self.prepare()
        submit_verdict(self.manifest, self.state, {**self.evidence['review_binding'], 'decision':'allow', 'justification':'fixture', 'risks':[]})
        self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_generic_once_missing_or_extra_confirmation_cannot_accept(self):
        self.prepare()
        self.record()
        for confirmation in ('sim', 'aprovado', CONVERSATION_CONFIRMATION, ''):
            with self.subTest(confirmation=confirmation):
                self.assertTrue(self.accept({**self.accept_args, 'confirmation': confirmation})['isError'])
        self.assertTrue(self.accept({k:v for k,v in self.accept_args.items() if k!='confirmation'})['isError'])
        self.assertTrue(self.accept({**self.accept_args, 'automatic':True})['isError'])
        self.assert_unchanged()

    def test_stale_binding_or_new_code_never_promotes(self):
        self.prepare()
        self.record()
        for key in ('review_id', 'reviewed_hash', 'dossier_hash'):
            self.assertTrue(self.accept({**self.accept_args, key:'0'*64})['isError'])
        (self.project/'server.py').write_text(fixtures.SERVER_SOURCE+'\n# newer\n', encoding='utf-8')
        self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_expired_allow_cannot_accept(self):
        self.prepare()
        self.record()
        path = self.state/'revisoes-de-atualizacoes'/(self.accept_args['review_id']+'.json')
        record = json.loads(path.read_text(encoding='utf-8'))
        record['decided_at'] = '2000-01-01T00:00:00+00:00'
        path.write_text(json.dumps(record), encoding='utf-8')
        self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_execution_configuration_cannot_be_accepted(self):
        self.prepare()
        self.manifest_data['configuration']['passthrough_names'] = ['NEW_VARIABLE']
        self.save_manifest()
        self.read()
        self.record()
        result = self.accept()
        self.assertTrue(result['isError'])
        self.assertIn('envelope', result['structuredContent']['reason'])
        self.assert_unchanged()

    def test_inspection_coverage_cannot_be_accepted(self):
        self.prepare()
        (self.project/'extra.py').write_text('value = 1\n')
        self.manifest_data['inspect_roots'].append('extra.py')
        self.save_manifest()
        self.read()
        self.record()
        self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_catalog_cannot_be_accepted(self):
        self.prepare()
        self.manifest_data['metadata']['tools'][0]['description'] = 'Changed description'
        self.save_manifest()
        self.read()
        self.record()
        result = self.accept()
        self.assertTrue(result['isError'])
        self.assertIn('catálogo', result['structuredContent']['reason'])
        self.assert_unchanged()

    def test_privacy_policy_cannot_be_promoted(self):
        from test_privacy_and_redaction import POLICY
        self.prepare()
        self.manifest_data['privacy_policy'] = POLICY
        self.save_manifest()
        self.read()
        self.record()
        self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_changed_baseline_during_acceptance_is_preserved(self):
        self.prepare()
        self.record()
        report = core.write_text_report
        changed = None
        def change_baseline(path, text):
            nonlocal changed
            report(path, text)
            if not path.name.startswith('version-acceptance-'):
                return
            old = json.loads(self.before)
            old['operator_note'] = 'concurrent edit'
            changed = core.canon(old)+b'\n'
            (self.state/'versao-aprovada.json').write_bytes(changed)
        with mock.patch('mcp_sentry_gateway.core.write_text_report', side_effect=change_baseline):
            self.assertTrue(self.accept()['isError'])
        self.assertEqual((self.state/'versao-aprovada.json').read_bytes(), changed)
        self.assertEqual(self.execution.backend.lifecycle.snapshot()['spawn_attempts'], 0)

    def test_missing_assessment_audit_cannot_accept(self):
        self.prepare()
        self.record()
        (self.state/'relatorios-de-seguranca'/f"review-{self.accept_args['review_id']}.txt").unlink()
        self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_required_audit_write_failure_never_changes_baseline(self):
        self.prepare()
        self.record()
        with mock.patch('mcp_sentry_gateway.core.write_text_report', side_effect=OSError('fixture disk failure')):
            self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_baseline_commit_failure_keeps_old_reference(self):
        self.prepare()
        self.record()
        write = core.write
        def fail_baseline(path, data):
            if path == self.state/'versao-aprovada.json':
                raise OSError('fixture baseline failure')
            return write(path, data)
        with mock.patch('mcp_sentry_gateway.core.write', side_effect=fail_baseline):
            self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_change_during_acceptance_audit_is_not_promoted(self):
        self.prepare()
        self.record()
        write_report = core.write_text_report
        def change_code(path, text):
            write_report(path, text)
            if not path.name.startswith('version-acceptance-'):
                return
            (self.project/'server.py').write_text(fixtures.SERVER_SOURCE+'\n# concurrent edit\n', encoding='utf-8')
        with mock.patch('mcp_sentry_gateway.core.write_text_report', side_effect=change_code):
            self.assertTrue(self.accept()['isError'])
        self.assert_unchanged()

    def test_audit_missing_after_acceptance_blocks_execution(self):
        self.prepare()
        self.record()
        self.accept()
        next((self.state/'relatorios-de-seguranca').glob('version-acceptance-*.txt')).unlink()
        self.assertEqual(self.echo()['structuredContent']['status'], 'security_blocked')
        self.assertEqual(self.execution.backend.lifecycle.snapshot()['spawn_attempts'], 0)

    def test_audit_tampering_after_acceptance_blocks_execution(self):
        self.prepare()
        self.record()
        self.accept()
        audit = next((self.state/'relatorios-de-seguranca').glob('version-acceptance-*.json'))
        audit.write_text('{}', encoding='utf-8')
        self.assertEqual(self.echo()['structuredContent']['status'], 'security_blocked')
        self.assertEqual(self.execution.backend.lifecycle.snapshot()['spawn_attempts'], 0)

    def test_acceptance_cannot_be_replayed(self):
        self.prepare()
        self.record()
        self.assertFalse(self.accept().get('isError', False))
        before = (self.state/'versao-aprovada.json').read_bytes()
        self.assertTrue(self.accept()['isError'])
        self.assertEqual((self.state/'versao-aprovada.json').read_bytes(), before)

    def test_concurrent_accept_and_once_cannot_commit_both_scopes(self):
        self.prepare()
        self.record()
        once = {**self.accept_args, 'confirmation': CONVERSATION_CONFIRMATION}
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.accept)
            second = pool.submit(self.tool, self.review, 'sentry_authorize_once', once)
            results = [first.result(), second.result()]
        self.assertEqual(sum(not r.get('isError', False) for r in results), 1)

    def test_old_running_backend_is_replaced_after_acceptance(self):
        core.approve(self.manifest, self.state)
        self.execution = StdioGateway(self.manifest, self.state, interface='execution', conversation_approval=True)
        self.addCleanup(lambda: self.execution.backend.close())
        self.assertEqual(self.echo('old')['content'][0]['text'], 'old')
        old_backend = self.execution.backend
        old_process = old_backend.process
        needle = 'os.environ.get("SERVER_GREETING", "")'
        self.assertIn(needle, fixtures.SERVER_SOURCE)
        (self.project/'server.py').write_text(fixtures.SERVER_SOURCE.replace(needle, '"new:"'), encoding='utf-8')
        self.review = StdioGateway(self.manifest, self.state, interface='review', conversation_approval=True)
        self.read()
        self.record()
        self.assertFalse(self.accept().get('isError', False))
        self.assertEqual(self.echo('value')['content'][0]['text'], 'new:value')
        self.assertIsNot(self.execution.backend, old_backend)
        self.assertIsNotNone(old_process.poll())


if __name__ == '__main__':
    unittest.main()
