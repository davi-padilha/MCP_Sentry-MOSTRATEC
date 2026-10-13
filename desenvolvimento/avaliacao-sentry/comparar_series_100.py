"""Compare frozen 0.11/1.0 reviews; publish aggregate transitions only."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz-privada', type=Path, required=True)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    root = args.raiz_privada.resolve()
    gold_path = root/'operador/reavaliacao-20261007/gabarito-revisado.csv'
    gold = {r['versao']: r['gabarito'] for r in read_csv(gold_path)}
    decisions, sources, freezes = {}, {}, {}
    for version in ('011', '100'):
        for effort in ('low', 'medium'):
            label = f'luna_{version}_{effort}'
            operator = root/f'series/luna-{effort}-{version}-20261007/operador'
            registry = operator/'execucoes/registro.csv'
            rows = [r for r in read_csv(registry) if r['repeticao'] in ('R1', 'R2')]
            assert len(rows) == 48 and len({(r['versao'], r['repeticao']) for r in rows}) == 48
            status = {}
            for row in rows:
                assert row['servidor_iniciado'] == 'nao'
                assert row['parecer_ia'] or row['inconclusivo'].strip()
                if row['inconclusivo'].strip():
                    result = 'inconclusivo'
                elif row['parecer_ia'] == gold[row['versao']]:
                    result = 'correto'
                else:
                    result = 'benigna_bloqueada' if gold[row['versao']] == 'liberar' else 'maligna_liberada'
                status[row['versao'], row['repeticao']] = result
            decisions[label] = status
            sources[label] = sha(registry)
            freezes[label] = json.loads((operator/'protocolo/congelamento.json').read_text(encoding='utf-8'))
    newest = freezes['luna_100_medium']
    for label, frozen in freezes.items():
        assert {r['versao']: r['sha256'] for r in frozen['patches']} == {r['versao']: r['sha256'] for r in newest['patches']}
        assert frozen['ordem_sha256'] == newest['ordem_sha256']
        assert frozen['pedidos_sha256'] == newest['pedidos_sha256']
        assert frozen['politicas_sha256'] == newest['politicas_sha256']
        assert frozen['gabarito_atual_sha256'] == sha(gold_path)
        assert set(decisions[label]) == set(decisions['luna_100_medium'])
    for version in ('011', '100'):
        assert freezes[f'luna_{version}_low']['wheel_sha256'] == freezes[f'luna_{version}_medium']['wheel_sha256']
    private_rows = [{'versao': v, 'repeticao': r, **{label: d[v, r] for label, d in decisions.items()}}
                    for v, r in sorted(decisions['luna_100_medium'])]
    transitions = []
    for before, after in [('luna_011_low', 'luna_100_low'),
                          ('luna_011_medium', 'luna_100_medium'),
                          ('luna_100_low', 'luna_100_medium')]:
        counts = Counter((decisions[before][key], decisions[after][key]) for key in decisions[before])
        assert sum(counts.values()) == 48
        transitions.extend({'antes': before, 'depois': after, 'resultado_antes': a,
                            'resultado_depois': b, 'unidades': n} for (a, b), n in sorted(counts.items()))
    totals = {label: dict(Counter(d.values())) for label, d in decisions.items()}
    payload = json.dumps({'totais': totals, 'transicoes': transitions})
    assert all(row['versao'] not in payload for row in private_rows)
    private = root/'series/luna-medium-100-20261007/operador/analise/comparacao-privada.json'
    write_json(private, {'fontes_sha256': sources, 'gabarito_sha256': sha(gold_path),
                         'casos': private_rows, 'transicoes': transitions, 'totais': totals})
    output = args.saida.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with (output/'comparacao_transicoes.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(transitions[0]))
        writer.writeheader()
        writer.writerows(transitions)
    write_json(output/'comparacao_proveniencia.json', {
        'gabarito': 'revisado-v2', 'gabarito_sha256': sha(gold_path), 'fontes_privadas_sha256': sources,
        'comparacao_privada_sha256': sha(private), 'patches_pedidos_ordem_politicas_iguais': True,
        'wheel_igual_entre_esforcos_de_cada_versao': True, 'totais': totals,
        'publicacao': 'Somente contagens agregadas; sem IDs originais, mapa entre IDs anonimos ou gabarito por caso.'})
    print(payload)


if __name__ == '__main__':
    main()
