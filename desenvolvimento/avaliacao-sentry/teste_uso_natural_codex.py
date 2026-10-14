"""Prepare/add an isolated Donna pair in Codex; preserve existing servers.

No discovery or new approval. Clone only the historical fixture reference;
the changed implementation starts pending. Connection defaults to preview.
"""
import argparse
import copy
import json
import tomllib
from pathlib import Path

from teste_uso_natural_claude import prepare as prepare_shared
from mcp_sentry_gateway.administration import installation_record, restore_codex
from mcp_sentry_gateway.core import digest
from mcp_sentry_gateway.setup import _save_config, _restore_config


def prepare(demo, destination, gateway_python):
    info = prepare_shared(demo, destination, True, gateway_python)
    config = json.loads((destination/'conectores.json').read_text('utf-8'))
    executor = config['mcpServers']['donna_mcp']
    for entry in config['mcpServers'].values():
        # Match the canonical Codex fragment, including argument order.
        entry['args'].remove('--conversation-approval')
        entry['args'].insert(entry['args'].index('mcp_sentry_gateway.gateway')+1,
                             '--conversation-approval')
    for name, filename in (('MCP_SECRETARY_AUDIT_FILE','auditoria.jsonl'),
                           ('MCP_SECRETARY_SIMULATED_STATE_FILE','estado.json'),
                           ('MCP_SECRETARY_MUTATION_STORE_FILE','acoes.json')):
        executor['env'][name] = str(destination/'dados-ficticios'/filename)
    # Keep this JSON alias for the shared SDK validator; actual Codex name is below.
    (destination/'conectores.json').write_text(json.dumps(config, indent=2)+'\n', encoding='utf-8')
    entries = {'donna_simulada':copy.deepcopy(executor),
               'mcp_sentry_review_donna_simulada':config['mcpServers']['mcp_sentry_review_donna_simulada']}
    entries['donna_simulada']['env_vars'] = list(executor['env'])
    lines = []
    for name, entry in entries.items():
        lines.extend([f'[mcp_servers.{json.dumps(name)}]',
                      'command = '+json.dumps(entry['command']),
                      'args = '+json.dumps(entry['args'])])
        if entry.get('env_vars'):
            lines.append('env_vars = '+json.dumps(entry['env_vars']))
        if entry.get('env'):
            lines.append('env = { '+', '.join(json.dumps(key)+' = '+json.dumps(value)
                                             for key,value in entry['env'].items())+' }')
        lines.append('')
    fragment = '\n'.join(lines)
    assert tomllib.loads(fragment)['mcp_servers'] == entries
    (destination/'conectores.toml').write_text(fragment, encoding='utf-8')
    info.update(client='codex', model_effort=None, model_selection='select_in_new_chat',
                execution_connector='donna_simulada',
                first_message='Use a Donna simulada para criar um rascunho para maria@example.test, assunto Reunião, mensagem: A reunião será amanhã às 14h.')
    (destination/'protocolo.json').write_text(json.dumps(info, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return info


def connect(destination, config, apply=False):
    checks = json.loads((destination/'validacao-transporte.json').read_text('utf-8'))
    assert checks['gateway_version'] == '1.3.1'
    assert checks['execution_blocked_before_spawn'] and checks['review_evidence_read']
    fragment = (destination/'conectores.toml').read_text('utf-8')
    additions = tomllib.loads(fragment)['mcp_servers']
    original = config.read_bytes()
    before = tomllib.loads(original.decode('utf-8'))
    existing = before.get('mcp_servers', {})
    if set(additions) & set(existing):
        raise ValueError('nome de teste já existe; nenhuma entrada será substituída')
    newline = '\r\n' if b'\r\n' in original else '\n'
    updated = original + (newline*2+fragment.replace('\n',newline)).encode('utf-8')
    expected = copy.deepcopy(before)
    expected.setdefault('mcp_servers', {}).update(additions)
    assert tomllib.loads(updated.decode('utf-8')) == expected
    result = {'status':'preview', 'added_connectors':list(additions),
              'existing_connectors_preserved':list(existing), 'preserves_other_options':True}
    if apply:
        receipt = destination/'codex-installation.json'
        if receipt.exists():
            raise ValueError('registro já existe; preserve a conexão anterior')
        backup = _save_config(config, original, updated)
        try:
            installation_record(config, backup, original, updated, 'donna_simulada', receipt)
        except Exception:
            _restore_config(config, original, updated)
            raise
        result.update(status='connected_restart_required', config=str(config), backup=str(backup),
                      backup_sha256=digest(original), installation_record=str(receipt))
        (destination/'conexao.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','connect','restore'))
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--demo', type=Path)
    parser.add_argument('--gateway-python', type=Path)
    parser.add_argument('--config', type=Path, default=Path.home()/'.codex/config.toml')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    destination = args.destination.resolve()
    if args.action == 'prepare':
        if args.demo is None or args.gateway_python is None:
            parser.error('--demo e --gateway-python requeridos')
        result = prepare(args.demo.resolve(), destination, args.gateway_python.resolve())
    elif args.action == 'connect':
        result = connect(destination, args.config.resolve(), args.apply)
    else:
        result = restore_codex(destination/'codex-installation.json', apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
