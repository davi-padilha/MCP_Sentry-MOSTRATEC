"""Audita a coleta congelada 0.11.0 e exporta somente campos públicos permitidos.

Não executa ferramentas, revisões ou aprovações. O gabarito e as conversas
ficam privados. A publicação usa IDs aleatórios sem mapa reversível publicado.
"""
import argparse
import csv
import hashlib
import hmac
import importlib.util
import json
import secrets
import statistics
import zipfile
from collections import Counter
from pathlib import Path

from medir_tokens_rollouts import read_rollout, tokens_of


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def distribution(values):
    return {"n": len(values), "min": min(values), "mediana": statistics.median(values),
            "media": statistics.mean(values), "max": max(values), "soma": sum(values)} if values else {"n": 0}


def rollout_path(original):
    if original.is_file():
        return original
    # Codex moves, rather than deletes, the rollout on reversible archiving.
    matches = list((Path.home() / ".codex/archived_sessions").rglob(original.name))
    assert len(matches) == 1, "rollout arquivado ausente ou ambiguo"
    return matches[0]


def consolidate(series, gold_path, output, verify_only=False):
    repo = Path(__file__).resolve().parents[2]
    protocol = series / "operador/protocolo"
    config = read_json(series / "operador/config.json")
    frozen = read_json(protocol / "congelamento.json")
    ready = read_json(protocol / "prontidao.json")
    # Use the frozen guards as well as independent file checks.
    spec = importlib.util.spec_from_file_location("operator_011", series / "operador/scripts/operar_bateria.py")
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    operator.require_authorization()
    effort = frozen["esforco"]
    assert frozen["modelo"] == "gpt-6-luna" and effort in ("low", "medium")
    assert config["ambiente"]["sentry_versao"] == "0.11.0"
    assert sha(protocol / "congelamento.json") == ready["congelamento_sha256"]
    assert sha(gold_path) == frozen["gabarito_atual_sha256"] == ready["gabarito_atual_sha256"]
    assert sha(protocol / "ordem_sorteada.csv") == frozen["ordem_sha256"]
    assert sha(protocol / "pedidos-fixos.json") == frozen["pedidos_sha256"]
    for patch in frozen["patches"]:
        assert sha(protocol / "patches" / (patch["versao"] + ".patch")) == patch["sha256"]
    wheel = repo / "pacote-usuario/mcp_sentry_gateway-0.11.0-py3-none-any.whl"
    assert sha(wheel) == frozen["wheel_sha256"] == config["ambiente"]["sentry_wheel_sha256"]
    installed = series / "instalacoes/sentry/Lib/site-packages"
    with zipfile.ZipFile(wheel) as package:
        modules = [name for name in package.namelist() if name.startswith("mcp_sentry_gateway/") and name.endswith(".py")]
        assert len(modules) == 16
        for name in modules:
            assert package.read(name) == (installed / name).read_bytes() == (repo / "desenvolvimento/gateway" / name).read_bytes()
    restoration = read_json(protocol / "restauracao-final.json")
    for reference in frozen["referencias"]:
        name = reference["servidor"]
        server = next(item for item in config["servidores"].values() if item["nome"] == name)
        family = name.removesuffix("_teste")
        assert restoration[family]["status"] == "ready" and not restoration[family]["issues"]
        for filename, digest in reference["hash_codigo_fonte_por_arquivo"].items():
            assert sha(Path(server["codigo"]) / filename) == digest
        state = Path(server["estado"])
        snapshot = Path(config["fotografias"]) / name / "estado"
        # Baseline and policy envelope must be byte-identical to the snapshot.
        for filename in ("versao-aprovada.json", "configuracao-de-execucao-aprovada.json"):
            assert (state / filename).read_bytes() == (snapshot / filename).read_bytes()
    registry = Path(config["registro"])
    rows = read_csv(registry)
    assert len(rows) >= 48 and len({row["id"] for row in rows}) == len(rows)
    primary = [row for row in rows if row["repeticao"] in ("R1", "R2")]
    order = read_csv(protocol / "ordem_sorteada.csv")
    assert [(r["versao"], r["repeticao"]) for r in primary] == [(r["versao"], r["repeticao"]) for r in order]
    assert len(primary) == 48
    gold = {r["versao"]: r["gabarito"] for r in read_csv(gold_path)}
    assert Counter(gold.values()) == {"liberar": 13, "bloquear": 11}
    key = secrets.token_bytes(32)
    public, private, turns_public, events_public = [], [], [], []
    event_dedup = set()
    for row in rows:
        folder = Path(row["evidencias"])
        audit = read_json(folder / "auditoria-conversa.json")
        evolution = read_json(folder / "evolucao-011.json")
        conversation = read_json(folder / "conversa.json")
        assert audit["modelo_esforco_confirmados"] and audit["pedidos_fixos_confirmados"]
        assert audit["aprovacao_inalterada"] and audit["envelope_inalterado"]
        assert audit["bloqueio_inicial"] and not audit["backend_iniciado"] and row["servidor_iniciado"] == "nao"
        assert all(c["model"] == "gpt-6-luna" and c["effort"] == effort for c in audit["contextos"])
        assert len(audit["contextos"]) == audit["turnos_completos"] == 3
        inconclusive = bool(row["inconclusivo"].strip())
        assert inconclusive == (not bool(row["parecer_ia"]))
        receipt = evolution["recibo"]
        if not inconclusive:
            assert evolution["recibo_confere_persistencia"] and receipt["persisted"]
            assert not receipt["execution_authorized"]
            assert receipt["decision"] == {"liberar": "allow", "bloquear": "block"}[row["parecer_ia"]]
        else:
            assert not receipt
        calls = conversation["chamadas_mcp"]
        registrations = [c for c in calls if c["tool"] == "sentry_record_assessment"]
        assert registrations or inconclusive
        last_registration = registrations[-1] if registrations else {"arguments": {}, "result": None}
        token_present = "review_token" in last_registration["arguments"]
        registration_errors = sum(c["status"] != "completed" or (c.get("result") or {}).get("isError", False) for c in registrations)
        outside = audit["chamadas_fora_roteiro"]
        assert all(c["tool"] in ("list_mcp_resources", "list_mcp_resource_templates") for c in outside)
        timing = audit["tempos_separados"]
        assert timing["available"]
        meta, turns, total = read_rollout(rollout_path(Path(audit["rollout_origem"])))
        assert meta["sessao"] == audit["thread_id"]
        assert len(turns) == 3 and not meta["herdados"]
        anonymous = hmac.new(key, row["versao"].encode(), hashlib.sha256).hexdigest()[:16]
        use = "diagnostico" if row["repeticao"] == "R3" else "principal"
        counts = Counter()
        for index, turn in enumerate(turns, 1):
            token = tokens_of(turn)
            assert token["fonte_tokens"] == "turn_token_usage"
            assert turn["model"] == "gpt-6-luna" and turn["effort"] == effort
            for field in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens"):
                counts[field] += token[field]
            turns_public.append({"caso_anonimo": anonymous, "repeticao": row["repeticao"], "uso": use,
                                 "servidor": row["servidor"], "turno": index, **token,
                                 "duracao_segundos": turn["duracao_ms"] / 1000,
                                 "primeiro_token_ms": turn["primeiro_token_ms"] if turn["primeiro_token_ms"] is not None else "",
                                 "mcp_chamadas": turn["mcp_chamadas"], "mcp_erros": turn["mcp_erros"]})
        assert total["total_tokens"] == counts["total_tokens"]
        public.append({"serie": "luna_" + effort + "_011", "caso_anonimo": anonymous, "repeticao": row["repeticao"],
                       "uso": use, "servidor": row["servidor"], "modelo": "gpt-6-luna", "esforco": effort, "sentry": "0.11.0",
                       "parecer_registrado": row["parecer_ia"], "inconclusivo": "sim" if inconclusive else "nao",
                       "backend_iniciado": "nao", "recibo_confere": "sim" if evolution["recibo_confere_persistencia"] else "nao",
                       "token_presente_no_registro": "sim" if token_present else "nao", "tentativas_registro": len(registrations),
                       "erros_registro": registration_errors, "chamadas_fora_roteiro": len(outside),
                       "tempo_operacional_min": row["tempo_min"], "duracao_turnos_segundos": timing["turn_duration_seconds"],
                       "pausas_entre_turnos_segundos": timing["between_turns_seconds"],
                       "intervalo_observado_segundos": timing["observed_interval_seconds"], **dict(counts)})
        for event in evolution["tempos_gateway"]:
            fingerprint = json.dumps(event, sort_keys=True)
            if fingerprint in event_dedup:
                continue
            event_dedup.add(fingerprint)
            for stage, duration in event["timings_ms"].items():
                events_public.append({"caso_anonimo": anonymous, "repeticao": row["repeticao"], "uso": use,
                                      "servidor": row["servidor"], "operacao": event["operation"], "etapa": stage, "duracao_ms": duration})
        private.append({"id": row["id"], "versao": row["versao"], "repeticao": row["repeticao"],
                        "caso_anonimo": anonymous, "esperado": gold[row["versao"]], "registrado": row["parecer_ia"],
                        "inconclusivo": inconclusive, "justificativa_persistida": receipt.get("justification", "") if receipt else "",
                        "chamadas_fora_roteiro": outside, "registro_argumentos": last_registration["arguments"],
                        "registro_resultado": last_registration.get("result"), "tentativas_registro": registrations,
                        "auditoria_sha256": sha(folder / "auditoria-conversa.json"),
                        "conversa_sha256": sha(folder / "conversa.json")})
    pairs = {}
    for r in primary:
        pairs.setdefault(r["versao"], {})[r["repeticao"]] = "inconclusivo" if r["inconclusivo"].strip() else r["parecer_ia"]
    discordant = {v for v, p in pairs.items() if p["R1"] != p["R2"]}
    assert {r["versao"] for r in rows if r["repeticao"] == "R3"} == discordant
    metrics = read_csv(series / "operador/analise/metricas.csv")
    overall = next(r for r in metrics if r["grupo"] == "TODAS")
    errors = [r for r in primary if r["parecer_ia"] and r["parecer_ia"] != gold[r["versao"]]]
    assert len(errors) == int(overall["benignas_bloqueadas"]) + int(overall["malignas_liberadas"])
    assert int(overall["inconclusivas"]) == sum(bool(r["inconclusivo"].strip()) for r in primary)
    assert int(overall["pares_concordantes"]) == len(pairs) - len(discordant)
    summary = {"primarias": len(primary), "diagnosticas": len(rows) - len(primary),
               "pareceres_persistidos_primarias": sum(bool(r["parecer_ia"]) for r in primary),
               "recibos_conferidos_primarias": sum(r["recibo_confere"] == "sim" for r in public if r["uso"] == "principal"),
               "malignas_bloqueadas": sum(gold[r["versao"]] == "bloquear" and r["parecer_ia"] == "bloquear" for r in primary),
               "malignas_liberadas": int(overall["malignas_liberadas"]),
               "benignas_liberadas": sum(gold[r["versao"]] == "liberar" and r["parecer_ia"] == "liberar" for r in primary),
               "benignas_bloqueadas": int(overall["benignas_bloqueadas"]), "inconclusivas": int(overall["inconclusivas"]),
               "acordos_gabarito": sum(r["parecer_ia"] == gold[r["versao"]] for r in primary),
               "pares_concordantes": int(overall["pares_concordantes"]), "pares": len(pairs),
               "conversas_com_desvio_roteiro": sum(bool(r["chamadas_fora_roteiro"]) for r in public),
               "primarias_com_erro_registro": sum(bool(r["erros_registro"]) for r in public if r["uso"] == "principal"),
               "erros_registro_primarias": sum(r["erros_registro"] for r in public if r["uso"] == "principal"),
               "tentativas_registro_primarias": sum(r["tentativas_registro"] for r in public if r["uso"] == "principal"),
               "backend_iniciado": False, "modelo_esforco_confirmados": True,
               "modulos_iguais_wheel_fonte_instalacao": len(modules), "codigo_nativo_e_aprovacoes_restaurados": True,
               "casos_pedidos_ordem_gabarito_preservados": True}
    # Check the exact allow-listed payload in memory before any file is written.
    payload = json.dumps({"execucoes": public, "turnos": turns_public, "gateway": events_public, "metricas": metrics}, ensure_ascii=False)
    for item in private:
        assert item["id"] not in payload and item["versao"] not in payload
        token = item["registro_argumentos"].get("review_token")
        assert not token or token not in payload
    assert "C:\\" not in payload and "rollout-" not in payload and "@" not in payload
    if verify_only:
        print(json.dumps({"auditoria": summary, "verificacao_publicacao": "payload em memoria apenas campos numericos, enums e IDs HMAC; sem caminhos, IDs originais ou tokens",
                          "campos_execucoes": list(public[0]), "campos_turnos": list(turns_public[0]), "campos_gateway": list(events_public[0])}, ensure_ascii=False))
        return
    private_dir = series / "operador/analise"
    write_json(private_dir / "consolidacao-privada.json", {"resumo": summary, "execucoes": private})
    output.mkdir(parents=True, exist_ok=True)
    for items in (public, turns_public, events_public):
        items.sort(key=lambda r: (r["caso_anonimo"], r["repeticao"], r.get("turno", 0), r.get("operacao", ""), r.get("etapa", "")))
    write_csv(output / "execucoes_publicas.csv", public)
    write_csv(output / "turnos_publicos.csv", turns_public)
    write_csv(output / "tempos_gateway.csv", events_public)
    write_csv(output / "metricas_por_grupo.csv", metrics)
    aggregates = {}
    for use in ("principal", "diagnostico"):
        selected = [r for r in public if r["uso"] == use]
        aggregates[use] = {field: distribution([float(r[field]) for r in selected]) for field in
                           ("duracao_turnos_segundos", "pausas_entre_turnos_segundos", "intervalo_observado_segundos", "tempo_operacional_min")}
        aggregates[use]["tokens"] = {field: sum(r[field] for r in selected) for field in
                                    ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")}
    for use in ("principal", "diagnostico"):
        aggregates[use]["gateway_por_etapa_ms"] = {stage: distribution([e["duracao_ms"] for e in events_public if e["uso"] == use and e["etapa"] == stage])
                                                  for stage in sorted({e["etapa"] for e in events_public})}
    write_json(output / "tempos-e-consumo.json", aggregates)
    provenance = {"schema_version": 1, "serie": "luna_" + effort + "_011", "modelo": "gpt-6-luna", "esforco": effort, "sentry": "0.11.0",
                  "wheel_sha256": sha(wheel), "gabarito_da_analise": "revisado-v2", "gabarito_sha256": sha(gold_path),
                  "conferencias": summary,
                  "fontes_privadas_sha256": {"registro.csv": sha(registry), "metricas.csv": sha(private_dir / "metricas.csv"),
                                             "auditoria-final.json": sha(private_dir / "auditoria-final.json"),
                                             "consolidacao-privada.json": sha(private_dir / "consolidacao-privada.json"),
                                             "congelamento.json": sha(protocol / "congelamento.json")},
                  "publicacao": {"ids": "HMAC com chave efemera nao publicada; mapa somente no arquivo privado de auditoria",
                                 "ordem": "por ID anonimo; nao representa ordem de execucao",
                                 "nao_incluido": ["gabarito por caso", "casos originais", "patches", "transcricoes", "justificativas", "credenciais", "contas", "caminhos", "IDs de conversas", "argumentos e retornos MCP"]}}
    provenance["arquivos_publicos_sha256"] = {p.name: sha(p) for p in output.iterdir() if p.suffix in (".csv", ".json") and p.name != "proveniencia.json"}
    write_json(output / "proveniencia.json", provenance)
    # No original identifiers/paths or token capabilities may enter public data.
    public_text = "\n".join(p.read_text(encoding="utf-8") for p in output.iterdir() if p.suffix in (".csv", ".json"))
    for item in private:
        assert item["id"] not in public_text
        token = item["registro_argumentos"].get("review_token")
        assert not token or token not in public_text
    assert "C:\\" not in public_text and "rollout-" not in public_text and "@" not in public_text
    print(json.dumps({"resumo": summary, "tempos_principais": aggregates["principal"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serie-privada", type=Path, required=True)
    parser.add_argument("--gabarito", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--verificar", action="store_true", help="Somente leituras e validacao do payload em memoria; nao grava arquivos.")
    args = parser.parse_args()
    consolidate(args.serie_privada.resolve(), args.gabarito.resolve(), args.saida.resolve(), args.verificar)
