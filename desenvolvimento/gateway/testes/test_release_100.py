"""Observed prototype issues: recoverable payloads and integrity-bound context."""
import json
import unittest

import test_usability_evolution as fixtures
from mcp_sentry_gateway.core import canon, digest, inspect


class ReleaseTests(unittest.TestCase):
    setUp = fixtures.RegistrationTests.setUp
    save_manifest = fixtures.RegistrationTests.save_manifest
    request = staticmethod(fixtures.RegistrationTests.request)
    prepare = fixtures.RegistrationTests.prepare
    call = fixtures.RegistrationTests.call
    args = fixtures.RegistrationTests.args
    def test_missing_token_is_recoverable_without_persisting_or_bypassing_read(self):
        evidence = self.prepare()
        result = self.call('sentry_record_assessment', {
            'decision': 'block', 'justification': 'controlled review', 'risks': []})
        error = result['structuredContent']
        self.assertTrue(result['isError'])
        self.assertEqual(error['code'], 'ASSESSMENT_FIELDS_MISSING')
        self.assertEqual(error['missing_fields'], ['review_token'])
        self.assertTrue(error['recoverable'])
        record = json.loads((self.state/'revisoes-de-atualizacoes'/(evidence['review_id']+'.json')).read_text())
        self.assertIsNone(record['verdict'])
        corrected = self.call('sentry_record_assessment', self.args(evidence['review_token']))
        self.assertTrue(corrected['structuredContent']['receipt']['persisted'])
        self.assertFalse(corrected['structuredContent']['receipt']['execution_authorized'])

    def test_mixed_format_reports_recovery_and_still_rejects_invalid_hash(self):
        evidence = self.prepare()
        legacy = {**evidence['review_binding'], 'decision': 'block', 'justification': 'fixture', 'risks': []}
        mixed = self.call('sentry_record_assessment', {**self.args(evidence['review_token']), 'verdict': legacy})
        self.assertEqual(mixed['structuredContent']['code'], 'ASSESSMENT_FORMAT_MIXED')
        self.assertTrue(mixed['structuredContent']['recoverable'])
        legacy['reviewed_hash'] = '0'*64
        invalid = self.call('sentry_record_assessment', {'verdict': legacy})
        self.assertEqual(invalid['structuredContent']['code'], 'REVIEW_BINDING_MISMATCH')

    def test_context_and_guidance_are_bound_and_do_not_claim_certification(self):
        evidence = self.prepare()
        dossier = inspect(self.manifest, self.state)['dossier']
        original_hash = dossier.pop('dossier_hash')
        self.assertEqual(digest(canon(dossier)), original_hash)
        self.assertEqual(evidence['review_guidance'], dossier['review_guidance'])
        self.assertIn('not privacy certification', dossier['review_guidance']['limits'])
        change = next(c for c in dossier['changes'] if c['path'] == 'server.py')
        self.assertEqual(change['context_lines'], 12)
        self.assertNotEqual(change['approved_sha256'], change['current_sha256'])
        dossier['review_guidance']['scope'] = 'different evidence'
        self.assertNotEqual(digest(canon(dossier)), original_hash)


if __name__ == '__main__':
    unittest.main()
