"""Validate a fresh, simulated chat trial without recording or approving it.

Requires a pending state produced by teste_uso_natural_claude.py and a Python
with the MCP SDK. Redirects fictional data into the new trial directory.
"""
import argparse
import asyncio
import hashlib
import json
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def verify(root, expected_version):
    info = json.loads((root/'protocolo.json').read_text('utf-8'))
    assert info['mode'] == 'simulated-safe' and info['conversation_approval_enabled']
    state = root/'state'
    record_path = state/'revisoes-de-atualizacoes'/f"{info['review_id']}.json"
    record = json.loads(record_path.read_text('utf-8'))
    assert record['status'] == 'pending' and record['verdict'] is None
    baseline = state/'versao-aprovada.json'
    baseline_before = baseline.read_bytes()
    assert json.loads(baseline_before)['integrity_hash'] != record['dossier']['current_hash']
    config = json.loads((root/'conectores.json').read_text('utf-8'))
    executor = config['mcpServers']['donna_mcp']
    reviewer = config['mcpServers']['mcp_sentry_review_donna_simulada']
    for name, filename in (('MCP_SECRETARY_AUDIT_FILE','auditoria.jsonl'),
                           ('MCP_SECRETARY_SIMULATED_STATE_FILE','estado.json'),
                           ('MCP_SECRETARY_MUTATION_STORE_FILE','acoes.json')):
        executor['env'][name] = str(root/'dados-ficticios'/filename)
    (root/'conectores.json').write_text(json.dumps(config, indent=2)+'\n', encoding='utf-8')

    def parameters(entry):
        assert '--conversation-approval' in entry['args']
        assert entry['args'][entry['args'].index('--store')+1] == str(state)
        return StdioServerParameters(command=entry['command'], args=entry['args'], env=entry.get('env',{}))

    async with stdio_client(parameters(executor)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.version == expected_version
            assert 'offer to review the change yourself' in initialized.instructions
            assert len((await session.list_tools()).tools) == 13
            response = await session.call_tool('criar_rascunho_email', {
                'destinatarios':['maria@example.test'], 'assunto':'Reunião',
                'mensagem':'A reunião será amanhã às 14h.'})
            blocked = response.structuredContent
            assert blocked['status'] == 'security_review_required' and not blocked['action_executed']
            assert blocked['review_interface'] == 'mcp_sentry_review_donna_simulada'
            assert blocked['review_offer']['requires_user_request']
            assert blocked['review_offer']['suggested_user_request'] == 'Faça a revisão sugerida.'
            (root/'resposta-bloqueio-tecnica.json').write_text(json.dumps(blocked, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assert not reviewer.get('env')
    async with stdio_client(parameters(reviewer)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.version == expected_version
            tools = (await session.list_tools()).tools
            assert len(tools) == 6
            assert {'sentry_accept_version','sentry_authorize_once'} <= {tool.name for tool in tools}
            evidence = (await session.call_tool(blocked['review_offer']['tool'], {})).structuredContent
            assert evidence['status'] == 'pending' and evidence['review_token']
            page = (await session.call_tool('sentry_review_evidence', {'review_id':evidence['review_id']})).structuredContent
            assert not page['has_more'] and page['total_changes'] == 1
    original = Path(info['original_review']).read_bytes()
    assert hashlib.sha256(original).hexdigest() == info['original_review_sha256']
    record = json.loads(record_path.read_text('utf-8'))
    assert record['status'] == 'pending' and record['verdict'] is None
    assert baseline.read_bytes() == baseline_before
    lifecycle = json.loads((state/'relatorios-de-seguranca/backend-lifecycle-current.json').read_text('utf-8'))
    assert lifecycle['spawn_attempts'] == 0
    checks = {'gateway_version':expected_version, 'execution_blocked_before_spawn':True,
              'review_evidence_read':True, 'complete_evidence_pagination':True,
              'conversation_approval_enabled':True, 'permanent_acceptance_available':True,
              'review_offer_present':True, 'execution_instructions_offer_review':True,
              'review_status':'pending', 'assessment_recorded':False,
              'execution_authorized':False, 'original_review_preserved':True,
              'simulated_data_isolated':True, 'real_model_tested':False}
    (root/'validacao-transporte.json').write_text(json.dumps(checks, indent=2)+'\n', encoding='utf-8')
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--expected-version', required=True)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(verify(args.destination.resolve(), args.expected_version))))
