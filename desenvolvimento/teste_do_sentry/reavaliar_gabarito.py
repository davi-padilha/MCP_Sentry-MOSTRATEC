"""Versiona uma reclassificacao autorizada e recalcula series ja executadas."""
import argparse
import csv
import hashlib
import io
import json
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from analisar import normalize, resultados, write_csv
from exportar_resultados_publicos import apply_revaluation


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def revaluate(root, target, public, version, previous, expected, reason):
    if target.exists():
        raise ValueError("A saida privada deve ser nova; nao sobrescrever uma reavaliacao existente.")
    if not target.is_relative_to(root / "operador"):
        raise ValueError("A saida privada deve ficar dentro da area do operador.")
    old = root / "operador/bateria-congelada-20261006/analise"
    gold = old / "gabarito-original.csv"
    sources = {
        "sol_081": (root / "operador/execucoes/registro.csv", old / "metricas.csv"),
        "luna_091": (root / "series/luna-091-20261006/operador/execucoes/registro.csv",
                     root / "series/luna-091-20261006/operador/analise/metricas.csv"),
    }
    original = read_csv(gold)
    revised = [dict(row) for row in original]
    selected = [row for row in revised if row["versao"] == version]
    assert len(original) == len({row["versao"] for row in original}) == 24
    assert len(selected) == 1 and selected[0]["gabarito"] == previous
    assert previous != expected and previous in {"liberar", "bloquear"} and expected in {"liberar", "bloquear"}
    selected[0]["gabarito"] = expected
    assert sum(before != after for before, after in zip(original, revised)) == 1
    protected = [gold, old / "auditoria-gabarito/mapeamento-original.md"]
    protected += [path for pair in sources.values() for path in pair]
    for folder in (root / "operador/patches", root / "operador/bateria-congelada-20261006/patches",
                   root / "series/luna-091-20261006/operador/protocolo/patches"):
        protected.extend(folder.glob("*.patch"))
    public_records = public / "execucoes_publicas.csv"
    protected.append(public_records)
    hashes = {path: sha(path) for path in protected}
    pointer = root / "operador/gabarito-atual.json"
    if pointer.exists():
        raise ValueError("Ja existe um gabarito atual versionado; conferir sua linhagem antes de criar outra revisao.")
    target.mkdir(parents=True)
    revised_gold = target / "gabarito-revisado.csv"
    write_csv(revised_gold, revised)
    old_key = {row["versao"]: row["gabarito"] for row in original}
    key = {row["versao"]: row["gabarito"] for row in revised}
    summaries, conclusions = {}, {}
    for series, (registry, historical_metrics) in sources.items():
        rows = read_csv(registry)
        assert len(rows) == (48 if series == "sol_081" else 49)
        with redirect_stdout(io.StringIO()) as output:
            resultados(registry, revised_gold, target / series / "metricas.csv")
        (target / series / "ANALISE-REVISADA.txt").write_text(output.getvalue(), encoding="utf-8")
        assessed = []
        for row in rows:
            case = row["versao"]
            verdict = "inconclusivo" if row["inconclusivo"].strip() else normalize(row["parecer_ia"])
            assessed.append({
                "versao": case, "repeticao": row["repeticao"],
                "gabarito_original": old_key[case], "gabarito_revisado": key[case],
                "parecer_registrado": row["parecer_ia"], "inconclusivo": row["inconclusivo"],
                "uso": "diagnostico" if row["repeticao"] == "R3" else "principal",
                "concorda_original": "sim" if verdict == old_key[case] else "nao",
                "concorda_revisado": "sim" if verdict == key[case] else "nao",
            })
        write_csv(target / series / "comparacao-por-execucao.csv", assessed)
        primary = [row for row in assessed if row["uso"] == "principal"]
        valid = [row for row in primary if not row["inconclusivo"]]
        assert len(primary) == 48
        metrics = read_csv(target / series / "metricas.csv")
        aggregate = next(row for row in metrics if row["grupo"] == "TODAS")
        historical = next(row for row in read_csv(historical_metrics) if row["grupo"] == "TODAS")
        for field in ("unidades", "inconclusivas", "pares", "pares_concordantes"):
            assert aggregate[field] == historical[field]
        summaries[series] = {
            "metricas_revisadas": aggregate,
            "pareceres_validos": len(valid),
            "concordantes_original": sum(row["concorda_original"] == "sim" for row in valid),
            "concordantes_revisado": sum(row["concorda_revisado"] == "sim" for row in valid),
            "backend_iniciado": any(row["servidor_iniciado"] != "nao" for row in rows),
        }
        conclusions[series] = [
            {"repeticao": row["repeticao"], "parecer_inalterado": row["parecer_ia"],
             "justificativa_original": row["justificativa_resumo"],
             "analise": reason}
            for row in rows if row["versao"] == version
        ]
        assert len(conclusions[series]) == 2
    assert all(sha(path) == digest for path, digest in hashes.items())
    manifest = {
        "schema_version": 1, "data": date.today().isoformat(), "gabarito_versao": "revisado-v2",
        "pos_coleta": True, "autorizada_pelo_operador": True,
        "autorizacao": "reavalie e faca as devidas alteracoes, alterando consequentemente tambem os resultados do sentry nos testes executados",
        "alteracoes": [{"versao": version, "antes": previous, "depois": expected, "motivo": reason}],
        "gabarito_original_sha256": sha(gold), "gabarito_revisado_sha256": sha(revised_gold),
        "originais_preservados": True, "novas_revisoes_executadas": False,
        "composicao": {"versoes": len(revised), "benignas": sum(row["gabarito"] == "liberar" for row in revised),
                       "malignas": sum(row["gabarito"] == "bloquear" for row in revised)},
        "conclusoes_do_caso": conclusions, "series": summaries,
        "fontes_originais_sha256": {str(path): digest for path, digest in hashes.items()},
    }
    (target / "reavaliacao.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "LEIA-ME.md").write_text(
        f"# Reavaliacao autorizada do gabarito\n\n{version}: {previous} -> {expected}.\n\n{reason}\n\n"
        "O gabarito-revisado.csv e o gabarito v2 vigente para estas analises. O CSV/ZIP original permanece como v1 historica. "
        "ANALISE-REVISADA.txt e metricas.csv recalculam as mesmas decisoes; comparacao-por-execucao.csv conserva a dupla leitura. "
        "R3 continua diagnostica e a tentativa parcial 0.9.0 permanece fora da comparacao. "
        "Nenhum prompt, patch, parecer, registro bruto ou estado de aprovacao foi alterado. "
        "A reclassificacao e posterior a coleta, nao valida universalmente os outros rotulos e nao isola o efeito de modelo/gateway/politicas.\n",
        encoding="utf-8")
    apply_revaluation(root, public, target)
    assert all(sha(path) == digest for path, digest in hashes.items())
    pointer.write_text(json.dumps({"gabarito_versao": "revisado-v2", "gabarito": str(revised_gold),
                                   "sha256": sha(revised_gold), "reavaliacao": str(target / "reavaliacao.json"),
                                   "uso": "reanalise das series executadas; nao altera protocolo congelado"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gabarito_versao": manifest["gabarito_versao"], "composicao": manifest["composicao"],
                      "originais_preservados": True, "series": summaries}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz-privada", type=Path, required=True)
    parser.add_argument("--saida-privada", type=Path, required=True)
    parser.add_argument("--saida-publica", type=Path, required=True)
    parser.add_argument("--versao", required=True)
    parser.add_argument("--de", choices=("liberar", "bloquear"), required=True)
    parser.add_argument("--para", choices=("liberar", "bloquear"), required=True)
    parser.add_argument("--motivo", required=True)
    args = parser.parse_args()
    revaluate(args.raiz_privada.resolve(), args.saida_privada.resolve(), args.saida_publica.resolve(),
              args.versao, args.de, args.para, args.motivo)
