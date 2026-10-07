"""Medição somente em leitura: não inicia backend, não copia nem persiste estado.
Execute com Python -B. Entradas privadas são opcionais e indicadas pelo operador.
A saída contém apenas contagens, hashes da fonte e tempos, nunca texto da evidência.
"""
import argparse
import ast
import hashlib
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'desenvolvimento/gateway/mcp_sentry_gateway'
sys.dont_write_bytecode = True
sys.path.insert(0, str(SOURCE.parent))
from mcp_sentry_gateway import core, gateway, mcp_facade, review


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def size(text):
    return {'characters': len(text), 'utf8_bytes': len(text.encode('utf-8')),
            'estimated_tokens_chars_div_4': round(len(text) / 4, 2),
            'real_provider_tokens': None}


def definitions(baseline):
    tools = []
    if baseline:
        tools = json.loads(baseline.read_text(encoding='utf-8'))['capture']['manifest']['metadata'].get('tools', [])
    wrapper = ('MCP server capability protected by MCP Sentry. It is a backend action '
               "and runs only when Sentry's integrity state permits it. ")
    protected = [{**t, 'description': wrapper + t.get('description', '')} for t in tools]
    result = {'catalog_supplied': baseline is not None, 'protected_tool_count': len(tools),
              'execution_original_catalog': size(compact({'tools': tools})),
              'execution_wrapped_catalog': size(compact({'tools': protected})),
              'wrapper_per_tool': size(wrapper),
              'review_external_tools': size(compact({'tools': mcp_facade.CONTROL_TOOLS})),
              'review_conversation_tools': size(compact({'tools': mcp_facade.CONTROL_TOOLS + [mcp_facade.CONVERSATION_AUTHORIZATION_TOOL]})),
              'tools': {t['name']: {'definition': size(compact(t)), 'description': size(t['description']),
                                  'input_schema': size(compact(t['inputSchema'])),
                                  'output_schema': size(compact(t['outputSchema']))}
                        for t in mcp_facade.CONTROL_TOOLS + [mcp_facade.CONVERSATION_AUTHORIZATION_TOOL]},
              'instructions': {name: size(getattr(gateway, name)) for name in (
                  'SERVER_INSTRUCTIONS', 'EXECUTION_INSTRUCTIONS', 'REVIEW_INSTRUCTIONS',
                  'CONVERSATION_EXECUTION_INSTRUCTIONS', 'CONVERSATION_REVIEW_INSTRUCTIONS')}}
    result['review_external_total_characters'] = result['review_external_tools']['characters'] + result['instructions']['REVIEW_INSTRUCTIONS']['characters']
    result['review_conversation_total_characters'] = result['review_conversation_tools']['characters'] + result['instructions']['CONVERSATION_REVIEW_INSTRUCTIONS']['characters']
    return result


def dossier_metrics(path):
    raw = path.read_text(encoding='utf-8')
    data = json.loads(raw)
    if 'result' in data:
        data = data['result']
    if 'structuredContent' in data:
        payload = data['structuredContent']
        origin = 'exported_tool_result'
    elif 'dossier' in data:
        d = data['dossier']
        payload = {'review_id': data.get('review_id', 'UNKNOWN_NOT_EXPORTED'),
                   'status': data.get('status', 'UNKNOWN_NOT_EXPORTED'),
                   'policy_version': data.get('policy_version', review.POLICY_VERSION),
                   **{k: d[k] for k in ('untrusted_content_notice', 'dossier_hash', 'current_hash',
                                       'baseline_hash', 'changes', 'metadata', 'configuration', 'privacy')},
                   'total_changes': len(d['changes']), 'coverage': d.get('coverage', {})}
        origin = 'reconstructed_from_record_not_exact_wire'
    else:
        payload = data
        origin = 'supplied_payload'
    if not isinstance(payload.get('changes'), list):
        raise ValueError('entrada não é um dossiê de revisão')
    payload = {k: v for k, v in payload.items() if k not in {'page', 'page_size', 'total_pages', 'has_more', 'next_page'}}
    fallback = compact(payload)
    return {'origin': origin, 'input_file': size(raw), 'payload_and_text_fallback': size(fallback),
            'mcp_tool_result_wire': size(compact(mcp_facade.MinimumMcp.tool_result(payload))),
            'changed_entries': len(payload['changes']),
            'diffs': size(''.join(c.get('diff', '') for c in payload['changes'])),
            'metadata': size(compact(payload.get('metadata', {}))),
            'configuration': size(compact(payload.get('configuration', {}))),
            'privacy': size(compact(payload.get('privacy', {})))}


def timed_capture(manifest):
    originals = core._capture_text, core.safe_text, core.digest
    totals = {'text_inclusive_sec': 0.0, 'redaction_sec': 0.0, 'hash_sec': 0.0,
              'text_calls': 0, 'redaction_calls': 0}
    def wrap(name, fn):
        def call(*a, **kw):
            start = time.perf_counter()
            try:
                return fn(*a, **kw)
            finally:
                totals[name + '_sec'] += time.perf_counter() - start
                if name == 'text_inclusive': totals['text_calls'] += 1
                if name == 'redaction': totals['redaction_calls'] += 1
        return call
    core._capture_text = wrap('text_inclusive', originals[0])
    core.safe_text = wrap('redaction', originals[1])
    core.digest = wrap('hash', originals[2])
    start = time.perf_counter()
    try:
        snapshot = core.capture(manifest)
    finally:
        elapsed = time.perf_counter() - start
        core._capture_text, core.safe_text, core.digest = originals
    # Redaction is nested within text for ordinary files; these columns are NOT additive.
    totals.update({'total_sec': elapsed, 'files_including_manifest': len(snapshot['files']),
                   'canonical_snapshot': size(core.canon(snapshot).decode('utf-8'))})
    return totals, snapshot


def verify_existing_copy(snapshot, directory):
    expected = {('manifest.json' if item['path'] == '@manifest' else item['path']): item['sha256'] for item in snapshot['files']}
    start = time.perf_counter()
    actual = {}
    links = 0
    for p in directory.rglob('*'):
        if p.is_symlink(): links += 1
        if p.is_file():
            actual[p.relative_to(directory).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    missing = expected.keys() - actual.keys()
    extra = actual.keys() - expected.keys()
    mismatched = sum(actual[k] != expected[k] for k in expected.keys() & actual.keys())
    return {'read_and_hash_existing_copy_sec': time.perf_counter() - start,
            'expected_files': len(expected), 'observed_files': len(actual),
            'missing_count': len(missing), 'extra_count': len(extra), 'mismatched_count': mismatched,
            'symlink_count': links,
            'note': 'Offline diagnostic only; not a reusable-copy execution gate, not an atomic snapshot.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, help='versao-aprovada.json indicado pelo operador')
    ap.add_argument('--dossier-small', type=Path, help='exportação já existente; não aplicar patches')
    ap.add_argument('--dossier-large', type=Path)
    ap.add_argument('--manifest', type=Path, help='mede duas capturas; NÃO chama inspect/security_status (persistem estado)')
    ap.add_argument('--verified-copy', type=Path, help='cópia existente, apenas releitura; requer --manifest')
    args = ap.parse_args()
    if args.verified_copy and not args.manifest: ap.error('--verified-copy requer --manifest')
    result = {'method': 'read_only_no_backend_no_config_write', 'python': sys.version.split()[0],
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.glob('*.py'))},
              'definitions': definitions(args.baseline),
              'limitations': ['chars/4 is a heuristic, not the model tokenizer or provider usage',
                             'MCP wire size is not model input size; client may transform or deduplicate',
                             'No protected-server process is started',
                             'copy writes and Node startup cannot be timed by a read-only script',
                             'cold capture means cold text cache, not necessarily cold OS/disk cache',
                             'timing wrappers add overhead; text and redaction columns overlap']}
    for label, path in [('small', args.dossier_small), ('large', args.dossier_large)]:
        if path: result['dossier_' + label] = dossier_metrics(path)
    if args.manifest:
        core._TEXT_CACHE.clear()
        core._TEXT_CACHE_BYTES = 0
        first, snap1 = timed_capture(args.manifest)
        second, snap2 = timed_capture(args.manifest)
        result['captures'] = {'first_cold_text_cache': first, 'second_warm_text_cache': second,
                              'same_snapshot': snap1 == snap2,
                              'note': 'These are capture measurements, not end-to-end inspect or start.'}
        if args.verified_copy:
            result['existing_copy'] = verify_existing_copy(snap2, args.verified_copy.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
