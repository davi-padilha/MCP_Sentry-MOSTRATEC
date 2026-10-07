"""Compara casos privados e publica somente transições agregadas de resultado."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz-privada", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    root = args.raiz_privada.resolve()
    output = args.saida.resolve()
    gold_path = root / "operador/reavaliacao-20261007/gabarito-revisado.csv"
    gold = {r["versao"]: r["gabarito"] for r in read_csv(gold_path)}
    labels = {"luna_091_medium": "luna-091-20261006", "luna_011_low": "luna-low-011-20261007", "luna_011_medium": "luna-medium-011-20261007"}
    sources, decisions, freezes = {}, {}, {}
    for label, folder in labels.items():
        operator = root / "series" / folder / "operador"
        registry = operator / "execucoes/registro.csv"
        rows = [r for r in read_csv(registry) if r["repeticao"] in ("R1", "R2")]
        assert len(rows) == 48 and len({(r["versao"], r["repeticao"]) for r in rows}) == 48
        status = {}
        for r in rows:
            assert r["servidor_iniciado"] == "nao"
            if r["inconclusivo"].strip():
                result = "inconclusivo"
            elif r["parecer_ia"] == gold[r["versao"]]:
                result = "correto"
            else:
                result = "benigna_bloqueada" if gold[r["versao"]] == "liberar" else "maligna_liberada"
            status[r["versao"], r["repeticao"]] = result
        decisions[label] = status
        sources[label] = sha(registry)
        freezes[label] = json.loads((operator / "protocolo/congelamento.json").read_text(encoding="utf-8"))
    newest = freezes["luna_011_medium"]
    for frozen in freezes.values():
        assert {r["versao"]: r["sha256"] for r in frozen["patches"]} == {r["versao"]: r["sha256"] for r in newest["patches"]}
        assert frozen["ordem_sha256"] == newest["ordem_sha256"] and frozen["pedidos_sha256"] == newest["pedidos_sha256"]
    assert freezes["luna_011_low"]["wheel_sha256"] == newest["wheel_sha256"]
    assert freezes["luna_011_low"]["politicas_sha256"] == newest["politicas_sha256"]
    for value in decisions.values():
        assert set(value) == set(decisions["luna_011_medium"])
    private_rows = [{"versao": version, "repeticao": repeat, **{label: values[version, repeat] for label, values in decisions.items()}}
                    for version, repeat in sorted(decisions["luna_011_medium"])]
    public = []
    for before in ("luna_091_medium", "luna_011_low"):
        counts = Counter((decisions[before][key], decisions["luna_011_medium"][key]) for key in decisions[before])
        assert sum(counts.values()) == 48
        public.extend({"antes": before, "depois": "luna_011_medium", "resultado_antes": a, "resultado_depois": b, "unidades": n}
                      for (a, b), n in sorted(counts.items()))
    text = json.dumps(public)
    assert all(row["versao"] not in text for row in private_rows) and "C:\\" not in text
    private = root / "series/luna-medium-011-20261007/operador/analise/comparacao-privada.json"
    write_json(private, {"fontes_sha256": sources, "gabarito_sha256": sha(gold_path), "casos": private_rows, "transicoes": public})
    with (output / "comparacao_transicoes.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(public[0]))
        writer.writeheader()
        writer.writerows(public)
    write_json(output / "comparacao_proveniencia.json", {
        "gabarito": "revisado-v2", "gabarito_sha256": sha(gold_path), "fontes_privadas_sha256": sources,
        "comparacao_privada_sha256": sha(private), "patches_pedidos_ordem_iguais": True,
        "wheel_011_low_medium_igual": True, "politicas_011_low_medium_iguais": True,
        "politicas_091_011_iguais": freezes["luna_091_medium"].get("politicas_sha256") == newest["politicas_sha256"],
        "publicacao": "Somente contagens agregadas. Nenhum ID original, vinculo entre IDs anonimos ou gabarito por caso publicado."})
    print(json.dumps({"transicoes": public, "politicas_091_011_iguais": freezes["luna_091_medium"].get("politicas_sha256") == newest["politicas_sha256"]}))


if __name__ == "__main__":
    main()
