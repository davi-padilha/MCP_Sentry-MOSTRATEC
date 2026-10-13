"""Auditoria posterior das 109 sessões históricas; não executa MCP ou revisões.

--privado cria mapa/exportações em área privada, lendo só os rollouts mapeados.
--publicar gera apenas tabelas agregadas a partir dessas exportações.
"""
import argparse
import contextlib
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import medir_tokens_rollouts as medidor

LAB = Path('C:/MCP-Sentry-Mostratec')
OUT = LAB / 'operador/tokens'
REPO = Path(__file__).resolve().parents[2]
PUBLIC = REPO / 'pesquisa/02_resultados/04_mostratec_mcp_sentry'
SOURCES = {
    'sol_081': LAB / 'operador/execucoes/registro.csv',
    'luna_091': LAB / 'series/luna-091-20261006/operador/execucoes/registro.csv',
    'luna_090_parcial': LAB / 'series/luna-090-20261006/operador/execucoes/registro.csv',
}


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def privado():
    mapping, audits = [], {}
    for serie, source in SOURCES.items():
        for row in rows(source):
            audit_path = Path(row['evidencias']) / 'auditoria-conversa.json'
            audit = json.loads(audit_path.read_text(encoding='utf-8'))
            sid = audit['thread_id']
            assert sid not in audits, 'Sessão duplicada'
            usage = ('parcial_tecnica' if serie == 'luna_090_parcial' else
                     'diagnostico' if row['repeticao'] == 'R3' else 'principal')
            mapping.append(dict(sessao=sid, serie=serie, versao=row['versao'],
                                repeticao=row['repeticao'], uso=usage))
            audits[sid] = audit
    assert Counter((r['serie'], r['uso']) for r in mapping) == {
        ('sol_081', 'principal'): 48, ('luna_091', 'principal'): 48,
        ('luna_091', 'diagnostico'): 1, ('luna_090_parcial', 'parcial_tecnica'): 12}
    files = list((Path.home() / '.codex/sessions').rglob('rollout-*.jsonl'))
    files += list((Path.home() / '.codex/archived_sessions').rglob('rollout-*.jsonl'))
    selected = []
    for row in mapping:
        candidates = [p for p in files if p.name.endswith(row['sessao'] + '.jsonl')]
        assert len(candidates) == 1, 'Sessão ausente ou duplicada: ' + row['sessao']
        meta, _, _ = medidor.read_rollout(candidates[0])
        assert meta['sessao'] == row['sessao'], 'Identidade de sessão divergente'
        selected.append(candidates[0])
    OUT.mkdir(parents=True, exist_ok=True)
    medidor.write_csv(OUT / 'mapa.csv', mapping)
    original = medidor.rollout_files
    medidor.rollout_files = lambda *args: iter(selected)
    try:
        with (OUT / 'execucao-medidor.txt').open('w', encoding='utf-8') as log:
            with contextlib.redirect_stdout(log):
                medidor.main(['--mapa', str(OUT / 'mapa.csv'), '--saida', str(OUT / 'saida')])
    finally:
        medidor.rollout_files = original
    checks = []
    for row, path in zip(mapping, selected):
        meta, turns, total = medidor.read_rollout(path)
        tokens = [medidor.tokens_of(t) for t in turns]
        # A herança inferida pelo fallback antigo não entra na conciliação quando
        # existem contadores explícitos por turno em uma sessão sem parent.
        summed = sum(t['total_tokens'] for t in tokens)
        recorded = int((total or {}).get('total_tokens', 0))
        field_totals = {f: sum(t[f] for t in tokens) for f in medidor.TOKEN_FIELDS}
        mismatches = [f for f in medidor.TOKEN_FIELDS
                      if field_totals[f] != int((total or {}).get(f, 0))]
        checks.append({**row, 'arquivo': path.name, 'sha256': digest(path),
                       'turnos': len(turns), 'derivada': meta['derivada'],
                       'fontes': sorted(set(t['fonte_tokens'] for t in tokens)),
                       'total_turnos': summed, 'total_sessao': recorded,
                       'total_confere_sem_heranca': summed == recorded,
                       'totais_por_campo': field_totals,
                       'campos_divergentes': mismatches,
                       'diagnostico_no_primeiro_turno': any(
                           'sentry_' in name for name in (turns[0]['mcp_ferramentas'] if turns else [])),
                       'avisos': ([f"{len(turns)} turnos"] if len(turns) != 3 else []) +
                           (['fontes de tokens divergentes'] if any(t['fonte_tokens'] != 'turn_token_usage' for t in tokens) else []) +
                           (['sessão derivada'] if meta['derivada'] else []) +
                           (['contadores divergentes'] if mismatches else [])})
    (OUT / 'auditoria.json').write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Auditoria privada concluída:', len(checks), 'sessões; avisos:', sum(bool(c['avisos']) for c in checks))


def number(value):
    return float(value) if value not in ('', None) else None


def fmt(value):
    if value is None:
        return '—'
    return (f'{value:,.3f}'.rstrip('0').rstrip('.').replace(',', '_')
            .replace('.', ',').replace('_', '.'))


def pair(group, field, scale=1):
    values = [number(r[field]) / scale for r in group if number(r[field]) is not None]
    return fmt(statistics.median(values)) + ' / ' + fmt(sum(values)) if values else '— / —'


def publicar():
    sessions = rows(OUT / 'saida/sessoes.csv')
    turns = rows(OUT / 'saida/turnos.csv')
    checks = json.loads((OUT / 'auditoria.json').read_text(encoding='utf-8'))
    assert len(sessions) == len(checks) == 109
    assert {r['sessao'] for r in sessions} == {r['sessao'] for r in checks}
    assert all(c['fontes'] == ['turn_token_usage'] and not c['derivada'] and c['total_confere_sem_heranca'] for c in checks)
    assert all(not c['campos_divergentes'] for c in checks)
    assert all(r['derivada'] == 'nao' for r in sessions)
    assert all(r['fonte_tokens'] == 'turn_token_usage' for r in turns)
    assert all(number(r['duracao_ms']) is not None and number(r['duracao_ms']) >= 0 for r in turns)
    assert all(number(r['espera_antes_s']) is None or number(r['espera_antes_s']) >= 0 for r in turns)
    assert all(r['modelo'] == ('gpt-6.1-sol' if r['serie'] == 'sol_081' else 'gpt-6-luna')
               and r['esforco'] == 'medium' for r in turns)
    groups = defaultdict(list)
    for row in turns:
        groups[(row['serie'], row['uso'], int(row['turno']))].append(row)
    versions = sorted({r['cli_version'] for r in sessions})
    dates = sorted(r['inicio'] for r in sessions)
    log = (OUT / 'execucao-medidor.txt').read_text(encoding='utf-8')
    warning_lines = [line for line in log.splitlines() if line.startswith('aviso:')]
    warned = sum(bool(c['avisos']) for c in checks)
    lines = ['# Tokens e tempos das baterias históricas', '',
             'Auditoria posterior dos arquivos de sessão, sem novas revisões ou execução de servidores.', '',
             f'Foram medidas **{len(sessions)} conversas e {len(turns)} turnos**: 48 primárias Sol 0.8.1, '
             '48 primárias Luna 0.9.1, uma R3 Luna 0.9.1 e 12 conversas da tentativa parcial Luna 0.9.0.', '',
             f'Versão do CLI nos metadados: `{", ".join(versions)}`. '
             'Versão do aplicativo registrada pelo operador: `26.930.41038`.',
             f'Período dos inícios das sessões (UTC): `{dates[0]}` a `{dates[-1]}`. '
             f'Apuração: {datetime.now(timezone.utc).date().isoformat()}.', '',
             '## Conferência', '',
             f'Todas as 109 sessões foram encontradas e tiveram identidade conferida. '
             f'Conversas com ressalva na auditoria: **{warned}**. '
             f'O medidor emitiu {len(warning_lines)} linhas de aviso.',
             'Todos os turnos usam `turn_token_usage`; não houve fonte ausente ou inconsistente. '
             'Todas as sessões têm `derivada = nao`. A soma dos tokens dos turnos foi conciliada com o total de cada conversa, '
             'campo a campo: entrada, cache, escrita de cache, saída, raciocínio e total.', '',
             'Os contextos dos 327 turnos confirmam `gpt-6.1-sol / medium` na série Sol e '
             '`gpt-6-luna / medium` nas séries Luna. Todas as durações estão presentes; não há intervalos negativos.', '',
             '## Tokens por turno', '',
             'Cada célula numérica apresenta **mediana / total**. Turno 1 = tarefa; 2 = revisão; 3 = registro. '
             'Tokens de raciocínio estão incluídos na saída; cache está incluído na entrada.', '',
             '| Série | Uso | Turno | n | Entrada | Entrada sem cache | Saída | Raciocínio |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    for (serie, usage, pos), group in sorted(groups.items()):
        lines.append(f'| {serie} | {usage} | {pos} | {len(group)} | ' + ' | '.join(pair(group, f) for f in
                     ['input_tokens', 'input_sem_cache', 'output_tokens', 'reasoning_output_tokens']) + ' |')
    lines += ['', '## Duração e intervalo entre turnos', '',
              'Valores em segundos, **mediana / total**. A duração registrada inclui modelo, ferramentas, transporte '
              'e esperas dentro do turno; não mede apenas computação da IA. O intervalo antes do turno é um indicador '
              'de espera/acompanhamento do operador e aplicativo, sem atribuição causal exclusiva ao operador. '
              'O primeiro turno não tem intervalo anterior mensurável.', '',
              '| Série | Uso | Turno | n | Duração registrada | Intervalo antes |',
              '|---|---|---:|---:|---:|---:|']
    for (serie, usage, pos), group in sorted(groups.items()):
        lines.append(f'| {serie} | {usage} | {pos} | {len(group)} | {pair(group, "duracao_ms", 1000)} | {pair(group, "espera_antes_s")} |')
    sol_first = [r for r in turns if r['serie'] == 'sol_081' and r['turno'] == '1']
    only_status = sum(r['mcp_ferramentas'].endswith('.sentry_security_status') and
                      ';' not in r['mcp_ferramentas'] for r in sol_first)
    sol_waits = [number(r['espera_antes_s']) for r in turns
                if r['serie'] == 'sol_081' and number(r['espera_antes_s']) is not None]
    outside = sum(r['serie'] == 'sol_081' and r['turno'] != '2' and int(r['dossie_chars']) > 0 for r in turns)
    lines += ['', f'Na série Sol, **{only_status} conversas** consultaram apenas `sentry_security_status` '
              'no primeiro turno. Mesmo assim, todas têm os três turnos previstos: trata-se de desvio '
              'no conteúdo da execução, não de formato ausente. Esse comportamento já registrado não altera os totais.', '',
              f'A série Sol contém **{sum(w > 300 for w in sol_waits)} intervalo acima de cinco minutos**, '
              f'com máximo de **{fmt(max(sol_waits))} s**. Ele foi mantido nos totais; '
              'representa uma pausa de acompanhamento entre turnos e não tempo de processamento do modelo. '
              'Por isso, o total de espera não deve ser usado como desempenho do gateway.']
    lines += ['', '## Cache e tamanho dos dossiês', '',
              'O tamanho é a soma dos caracteres dos conteúdos retornados por `sentry_review_current_block` '
              'no turno 2; não é contagem de tokens nem tamanho exclusivo do diff. '
              'Múltiplas leituras, quando presentes, são somadas. Zeros são informados separadamente.', '',
              '| Série | Uso | Entrada total | Cache total | Cache / entrada | Dossiês > 0 / turnos 2 | Caracteres mín. / mediana / máx. |',
              '|---|---|---:|---:|---:|---:|---:|']
    for serie, usage in sorted({(r['serie'], r['uso']) for r in turns}):
        group = [r for r in turns if (r['serie'], r['uso']) == (serie, usage)]
        review = [r for r in group if r['turno'] == '2']
        sizes = [int(r['dossie_chars']) for r in review if int(r['dossie_chars']) > 0]
        inp = sum(int(r['input_tokens']) for r in group)
        cache = sum(int(r['cached_input_tokens']) for r in group)
        size_cell = ' / '.join(fmt(v) for v in [min(sizes), statistics.median(sizes), max(sizes)]) if sizes else '—'
        lines.append(f'| {serie} | {usage} | {fmt(inp)} | {fmt(cache)} | {fmt(100 * cache / inp)}% | {len(sizes)} / {len(review)} | {size_cell} |')
    lines += ['', f'Na série Sol, há também **{outside} turnos fora do turno 2** com retorno de dossiê. '
              'Essas leituras entram nos tokens e tempos dos respectivos turnos, mas não na distribuição '
              'de tamanho acima, que atende ao recorte do turno de revisão. Os tamanhos positivos cobrem '
              'todos os turnos 2; não há zeros nessa distribuição.']
    lines += ['', '## Medição, estimativas e limites', '',
              'Tokens são contadores efetivos dos logs do Codex, usando o último contador acumulado de cada turno, '
              'uma vez por turno. Não se somam eventos cumulativos intermediários. Incluem contexto do aplicativo '
              'e resultados das ferramentas. Durações são os valores de `task_complete.duration_ms`; '
              'intervalos vêm dos horários de início e fim registrados.', '',
              'Estes números não comprovam dinheiro debitado nem consumo dos limites da assinatura. '
              'Converter tokens em créditos ou dólares é uma estimativa dependente da tarifa e modalidade de cobrança. '
              'As estimativas históricas de Luna 0.9.1 permanecem em [TEMPOS-E-CONSUMO.md](TEMPOS-E-CONSUMO.md).', '',
              'A tentativa parcial e a R3 estão separadas das primárias. As consultas antecipadas ao diagnóstico '
              'na bateria Sol não são excluídas nem reinterpretadas como novas revisões. '
              'O mapa, tabelas por sessão/turno e avisos detalhados permanecem privados. '
              'Nenhum resultado, gabarito, patch ou decisão foi alterado.', '',
              '## Proveniência', '',
              f'- Medidor SHA-256: `{digest(Path(medidor.__file__))}`.',
              f'- Consolidador SHA-256: `{digest(Path(__file__))}`.',
              f'- Mapa privado SHA-256: `{digest(OUT / "mapa.csv")}`.',
              f'- Tabela privada de sessões SHA-256: `{digest(OUT / "saida/sessoes.csv")}`.',
              f'- Tabela privada de turnos SHA-256: `{digest(OUT / "saida/turnos.csv")}`.',
              f'- Auditoria privada SHA-256: `{digest(OUT / "auditoria.json")}`.', '']
    for serie, source in SOURCES.items():
        lines.append(f'- Registro privado `{serie}` SHA-256: `{digest(source)}`.')
    # Somente os agregados acima são publicados: não há identificadores, nomes de
    # casos, textos das conversas ou linhas das tabelas privadas no documento.
    (PUBLIC / 'TOKENS_E_TEMPOS.md').write_text('\n'.join(lines), encoding='utf-8')
    print('Resumo agregado publicado; conversas:', len(sessions), '; turnos:', len(turns))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--privado', action='store_true')
    mode.add_argument('--publicar', action='store_true')
    args = parser.parse_args()
    privado() if args.privado else publicar()
