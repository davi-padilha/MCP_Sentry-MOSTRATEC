"""SDK fixture: permanent acceptance and Donna's two-call draft workflow.

Requires the existing simulated Donna demo. Never connects a desktop client;
consent/assessment below are test inputs, not a model verdict or user approval.
"""
import argparse
import asyncio
import hashlib
import json
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from teste_uso_natural_claude import prepare


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


async def verify(demo, destination, python):
    source = demo/'servidor/server.py'
    assert 'os.environ["MCP_SECRETARY_MODE"] = "simulated-safe"' in source.read_text('utf-8')
    original_state = demo/'estados/donna_simulada/state'
    original_files = {path: path.read_bytes() for path in original_state.rglob('*') if path.is_file()}
    source_before = source.read_bytes()
    prepare(demo, destination, conversation_approval=True, gateway_python=python)
    entries = json.loads((destination/'conectores.json').read_text('utf-8'))['mcpServers']
    executor, reviewer = entries['donna_mcp'], entries['mcp_sentry_review_donna_simulada']
    for name, filename in (('MCP_SECRETARY_AUDIT_FILE', 'auditoria.jsonl'),
                           ('MCP_SECRETARY_SIMULATED_STATE_FILE', 'estado.json'),
                           ('MCP_SECRETARY_MUTATION_STORE_FILE', 'acoes.json')):
        executor['env'][name] = str(destination/'dados-ficticios'/filename)
    dump(destination/'conectores.json', {'mcpServers':entries})

    def params(entry):
        return StdioServerParameters(command=entry['command'], args=entry['args'], env=entry.get('env', {}))

    state = destination/'state'
    baseline_before = (state/'versao-aprovada.json').read_bytes()
    envelope_before = (state/'configuracao-de-execucao-aprovada.json').read_bytes()
    arguments = {'destinatarios':['maria@example.test'], 'assunto':'Reunião',
                 'mensagem':'A reunião será amanhã às 14h.'}
    async with stdio_client(params(executor)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            result = await session.call_tool('criar_rascunho_email', arguments)
            assert result.structuredContent['status'] == 'security_review_required'
    assert json.loads((state/'relatorios-de-seguranca/backend-lifecycle-current.json').read_text('utf-8'))['spawn_attempts'] == 0
    async with stdio_client(params(reviewer)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            assert len(tools) == 6
            evidence = (await session.call_tool('sentry_review_current_block', {})).structuredContent
            recorded = await session.call_tool('sentry_record_assessment', {
                'review_token': evidence['review_token'], 'decision':'allow',
                'justification':'SDK fixture only; not a model assessment or live user consent.', 'risks':[]})
            assert not recorded.isError and recorded.structuredContent['approval_scope_required']
            assert (state/'versao-aprovada.json').read_bytes() == baseline_before
            accept = next(tool for tool in tools if tool.name == 'sentry_accept_version')
            accepted = await session.call_tool('sentry_accept_version', {
                'review_id':evidence['review_id'], 'reviewed_hash':evidence['current_hash'],
                'dossier_hash':evidence['dossier_hash'],
                'confirmation':accept.inputSchema['properties']['confirmation']['const']})
            assert not accepted.isError and accepted.structuredContent['status'] == 'version_accepted'
            assert accepted.structuredContent['backend_started'] is False
            dump(destination/'recibo-aceitacao-fixture.json', accepted.structuredContent)
    assert (state/'configuracao-de-execucao-aprovada.json').read_bytes() == envelope_before
    assert json.loads((state/'versao-aprovada.json').read_text('utf-8'))['integrity_hash'] == evidence['current_hash']
    async with stdio_client(params(executor)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            preview = await session.call_tool('criar_rascunho_email', arguments)
            assert not preview.isError and preview.structuredContent['status'] == 'confirmation_required'
            arguments['confirmacao_id'] = preview.structuredContent['confirmation_id']
            created = await session.call_tool('criar_rascunho_email', arguments)
            assert not created.isError and created.structuredContent['status'] == 'draft'
            assert created.structuredContent['confirmation']['status'] == 'executed'
            assert not (await session.call_tool('descrever_donna', {})).isError
    async with stdio_client(params(executor)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            replay = await session.call_tool('criar_rascunho_email', arguments)
            assert not replay.isError and replay.structuredContent['confirmation']['idempotent_replay']
            assert replay.structuredContent['id'] == created.structuredContent['id']
    drafts = json.loads((destination/'dados-ficticios/estado.json').read_text('utf-8'))['drafts']
    assert len(drafts) == 1 and drafts[0]['recipients'] == ['maria@example.test']
    assert source.read_bytes() == source_before
    assert all(path.read_bytes() == data for path, data in original_files.items())
    assert set(original_files) == {path for path in original_state.rglob('*') if path.is_file()}
    report = {'fixture_only':True, 'real_model_tested':False, 'google_actions':0,
              'blocked_before_spawn':True, 'recording_did_not_change_baseline':True,
              'permanent_acceptance_did_not_start_backend':True, 'execution_envelope_unchanged':True,
              'preview_then_confirmed_draft':True, 'repeated_call_after_acceptance':True,
              'reconnected_without_new_approval':True, 'replay_did_not_duplicate_draft':True,
              'original_evidence_and_source_preserved':True,
              'accepted_hash':evidence['current_hash'],
              'original_source_sha256':hashlib.sha256(source_before).hexdigest()}
    dump(destination/'validacao-aceitacao-permanente.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--gateway-python', required=True, type=Path)
    args = parser.parse_args()
    asyncio.run(verify(args.demo.resolve(), args.destination.resolve(), args.gateway_python.resolve()))
