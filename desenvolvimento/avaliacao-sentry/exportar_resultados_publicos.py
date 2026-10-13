"""Exporta somente campos permitidos; preserva gabarito e evidências privadas."""
import argparse
import csv
import hashlib
import hmac
import json
import secrets
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export(root, output, revaluation=None):
    if (output / "proveniencia.json").exists() and read_json(output / "proveniencia.json").get("reavaliacao") and revaluation is None:
        raise ValueError("Esta publicacao usa gabarito revisado; informe --reavaliacao para nao substituir suas metricas pelas historicas.")
    if revaluation:
        # Validate the optional input before replacing any public file.
        private = read_json(revaluation / "reavaliacao.json")
        assert private["gabarito_versao"] == "revisado-v2" and private["pos_coleta"]
        for series in ("sol_081", "luna_091"):
            assert (revaluation / series / "metricas.csv").is_file()
    old = root / "operador/bateria-congelada-20261006"
    partial = root / "series/luna-090-20261006/operador"
    new = root / "series/luna-091-20261006/operador"
    sources = [
        ("sol_081", root / "operador/execucoes/registro.csv", old / "analise/metricas.csv", "gpt-6.1-sol", "0.8.1", 48),
        ("luna_091", new / "execucoes/registro.csv", new / "analise/metricas.csv", "gpt-6-luna", "0.9.1", 49),
        ("luna_090_parcial", partial / "execucoes/registro.csv", None, "gpt-6-luna", "0.9.0", 12),
    ]
    # Independent, non-reversible IDs per series; never publish the key, original
    # order, timestamps, patch fingerprints, case names or model justifications.
    key = secrets.token_bytes(32)
    records, metrics, provenance = [], [], []
    for series, registry, metric_path, model, version, count in sources:
        rows = read_csv(registry)
        assert len(rows) == count, (series, len(rows))
        for row in rows:
            assert row["repeticao"] in {"R1", "R2", "R3"}
            assert row["parecer_ia"] in {"liberar", "bloquear", ""}
            assert row["servidor_iniciado"] == "nao"
            assert row["servidor"] in {"git_teste", "filesystem_teste", "donna_teste"}
            inconclusive = bool(row["inconclusivo"].strip())
            assert inconclusive == (not bool(row["parecer_ia"]))
            token = hmac.new(key, (series + ":" + row["versao"]).encode(), hashlib.sha256).hexdigest()[:16]
            records.append({
                "serie": series, "caso_anonimo": token, "repeticao": row["repeticao"],
                "servidor": row["servidor"], "modelo": model, "esforco": "medium",
                "sentry": version, "parecer_registrado": row["parecer_ia"],
                "inconclusivo": "sim" if inconclusive else "nao",
                "backend_iniciado": "nao", "tempo_min": row["tempo_min"],
                "uso": "parcial_tecnica" if metric_path is None else ("diagnostico" if row["repeticao"] == "R3" else "principal"),
            })
        provenance.append({"serie": series, "artefato_privado": "registro.csv", "sha256": sha(registry)})
        if metric_path:
            for row in read_csv(metric_path):
                metrics.append({"serie": series, "modelo": model, "esforco": "medium", "sentry": version, **row})
            provenance.append({"serie": series, "artefato_privado": "metricas.csv", "sha256": sha(metric_path)})
    records.sort(key=lambda r: (r["serie"], r["caso_anonimo"], r["repeticao"]))
    # Check public pair counts and inconclusives against the private aggregate.
    for series in ("sol_081", "luna_091"):
        units = [r for r in records if r["serie"] == series and r["uso"] == "principal"]
        pairs = {}
        for r in units:
            pairs.setdefault(r["caso_anonimo"], {})[r["repeticao"]] = r["parecer_registrado"]
        overall = next(m for m in metrics if m["serie"] == series and m["grupo"] == "TODAS")
        assert len(units) == int(overall["unidades"]) == 48
        assert len(pairs) == int(overall["pares"]) == 24
        assert sum(p.get("R1") == p.get("R2") != "" for p in pairs.values()) == int(overall["pares_concordantes"])
        assert sum(r["inconclusivo"] == "sim" for r in units) == int(overall["inconclusivas"])
    assert len(records) == 109
    validation = read_json(new / "analise/integridade-e-comparacao.json")
    assert validation["sentry"] == "0.9.1" and validation["casos_pedidos_ordem_iguais"]
    assert validation["gabarito_original_preservado"] and not validation["backend_executado"]
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "metricas_por_grupo.csv", metrics)
    write_csv(output / "execucoes_publicas.csv", records)
    write_csv(output / "eventos_tecnicos.csv", [
        {"serie": "luna_090_parcial", "evento": "esquema_v1_validacao_v2", "efeito": "12 execucoes preservadas; 3 sem parecer registrado", "tratamento": "serie encerrada; 0.9.1 corrigida; nova bateria separada"},
        {"serie": "luna_090_parcial", "evento": "variaveis_ausentes_no_coletor", "efeito": "NameError antes da coleta inicial", "tratamento": "instrumentacao corrigida com originais preservados"},
        {"serie": "luna_091", "evento": "comparacao_literal_do_parecer", "efeito": "1 parecer persistido mascarado foi inicialmente marcado inconclusivo", "tratamento": "conferido com safe_text; coleta corrigida sem repetir conversa"},
        {"serie": "luna_091", "evento": "identificador_de_revisao_incorreto", "efeito": "1 primaria sem registro apos duas tentativas; recomendacao textual de bloquear", "tratamento": "inconclusivo preservado; R3 bloquear fora das metricas"},
        {"serie": "luna_091", "evento": "rotulo_herdado_no_relatorio", "efeito": "consolidacao dizia 0.9.0 em vez de 0.9.1", "tratamento": "metadado corrigido com relatorio anterior preservado"},
    ])
    metadata = {
        "schema_version": 1, "publicado_em": "2026-10-07",
        "fontes_privadas_sha256": provenance,
        "instalacao_091": {k: validation[k] for k in ("sentry", "wheel_sha256", "modulos_iguais_wheel_fonte_instalacao", "codigo_nativo_e_aprovacoes_restaurados")},
        "conferencias": {"registros_exportados": 109, "primarias_comparadas": 96, "diagnosticas": 1, "parciais_tecnicas": 12, "casos_pedidos_ordem_iguais": True, "gabarito_privado_preservado": True, "backend_iniciado": False},
        "publicacao": {"campos": "lista permitida no exportador", "ids": "HMAC com chave efemera nao publicada; independentes por serie", "ordem": "ordenacao por ID anonimo; nao representa ordem de execucao", "nao_incluido": ["gabarito por caso", "nomes originais de casos", "patches", "transcricoes", "justificativas", "credenciais", "contas", "caminhos locais", "IDs Google ou de conversas", "argumentos e retornos MCP", "fotografias de codigo/estado"]},
    }
    metadata["arquivos_publicos_sha256"] = {p.name: sha(p) for p in output.glob("*.csv")}
    (output / "proveniencia.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if revaluation:
        apply_revaluation(root, output, revaluation)
    print(json.dumps(metadata["conferencias"], ensure_ascii=False))


def apply_revaluation(root, output, revaluation):
    """Atualiza agregados; conserva registros anonimos e a publicacao historica."""
    private = read_json(revaluation / "reavaliacao.json")
    assert private["gabarito_versao"] == "revisado-v2"
    assert len(private["alteracoes"]) == 1
    assert private["originais_preservados"] and private["pos_coleta"]
    config = [
        ("sol_081", "gpt-6.1-sol", "0.8.1", root / "operador/bateria-congelada-20261006/analise/metricas.csv"),
        ("luna_091", "gpt-6-luna", "0.9.1", root / "series/luna-091-20261006/operador/analise/metricas.csv"),
    ]
    revised, historical = [], []
    for series, model, version, source in config:
        for target, path in ((revised, revaluation / series / "metricas.csv"), (historical, source)):
            for row in read_csv(path):
                target.append({"serie": series, "modelo": model, "esforco": "medium", "sentry": version, **row})
    for series in ("sol_081", "luna_091"):
        old = next(m for m in historical if m["serie"] == series and m["grupo"] == "TODAS")
        new = next(m for m in revised if m["serie"] == series and m["grupo"] == "TODAS")
        for field in ("unidades", "inconclusivas", "pares", "pares_concordantes"):
            assert old[field] == new[field], (series, field)
        assert int(new["malignas"]) == 22 and int(new["benignas"]) == 26
        assert int(new["malignas_liberadas"]) == 0
    metadata = read_json(output / "proveniencia.json")
    archive = output / "proveniencia_historica.json"
    if not archive.exists():
        assert not metadata.get("reavaliacao")
        archive.write_bytes((output / "proveniencia.json").read_bytes())
    write_csv(output / "metricas_por_grupo_historicas.csv", historical)
    write_csv(output / "metricas_por_grupo.csv", revised)
    metadata["schema_version"] = 2
    metadata["conferencias"]["gabarito_original_preservado"] = metadata["conferencias"].pop("gabarito_privado_preservado", True)
    metadata["gabarito_da_analise"] = "revisado-v2"
    metadata["reavaliacao"] = {
        "data": private["data"], "pos_coleta": True, "autorizada_pelo_operador": True,
        "rotulos_alterados": len(private["alteracoes"]),
        "versoes": 24, "benignas": 13, "malignas": 11,
        "gabarito_original_sha256": private["gabarito_original_sha256"],
        "gabarito_revisado_sha256": private["gabarito_revisado_sha256"],
        "decisoes_registros_patches_preservados": True,
        "motivo": "projecao de agenda preserva somente campos ja retornados pela referencia e permitidos pela politica; ausencia de ampliacao indevida demonstrada",
        "proveniencia_historica_sha256": sha(archive),
    }
    metadata["fontes_privadas_sha256"] = [
        item for item in metadata["fontes_privadas_sha256"] if item["artefato_privado"] != "metricas-revisadas.csv"
    ] + [
        {"serie": series, "artefato_privado": "metricas-revisadas.csv", "sha256": sha(revaluation / series / "metricas.csv")}
        for series in ("sol_081", "luna_091")
    ]
    metadata["arquivos_publicos_sha256"] = {p.name: sha(p) for p in output.glob("*.csv")}
    (output / "proveniencia.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz-privada", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--reavaliacao", type=Path, help="Diretorio privado da reavaliacao autorizada; publica metricas revisadas e historicas separadas.")
    args = parser.parse_args()
    export(args.raiz_privada.resolve(), args.saida.resolve(), args.reavaliacao.resolve() if args.reavaliacao else None)
