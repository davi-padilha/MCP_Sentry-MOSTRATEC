"""Prepara cada revisão do Teste do MCP Sentry.

Comandos:
  fotografar  guarda o código e o estado aprovados de um servidor (uma vez)
  sortear     gera a ordem sorteada das revisões R1/R2
  preparar    restaura código e estado, aplica o patch e cria a pasta de evidências
  coletar     copia os registros do Sentry para a pasta de evidências
  restaurar   volta código e estado à versão de referência

O script não conhece o gabarito nem o conteúdo das versões.
"""
import argparse
import csv
import hashlib
import json
import random
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

APPROVED_VERSION_FILE = "versao-aprovada.json"
STATE_DIRS_TO_COLLECT = ("relatorios-de-seguranca", "revisoes-de-atualizacoes", "conexoes-observadas")
VERSIONS_PER_SERVER = 8
REGISTRY_FIELDS = (
    "id", "servidor", "versao", "repeticao", "preparado_em", "patch_sha256",
    "servidor_iniciado", "parecer_ia", "justificativa_resumo", "inconclusivo",
    "tempo_min", "dificuldades", "evidencias",
)


class PreparoError(Exception):
    pass


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("servidores", "fotografias", "patches", "evidencias", "registro"):
        if key not in config:
            raise PreparoError(f"configuração sem o campo '{key}'")
    return config


def server_for(config, prefix):
    try:
        server = config["servidores"][prefix]
    except KeyError as exc:
        raise PreparoError(f"servidor '{prefix}' não está na configuração") from exc
    return server["nome"], Path(server["codigo"]), Path(server["estado"])


def snapshot_dirs(config, name):
    base = Path(config["fotografias"]) / name
    return base / "codigo", base / "estado"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_dir(source, target):
    """Replace target with a copy of source; both must be configured paths."""
    if not source.is_dir():
        raise PreparoError(f"fotografia ausente: {source}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def snapshot(config, prefix):
    name, code, state = server_for(config, prefix)
    snap_code, snap_state = snapshot_dirs(config, name)
    if snap_code.exists() or snap_state.exists():
        raise PreparoError(f"fotografia de {name} já existe; apague-a manualmente para refazer")
    if not (state / APPROVED_VERSION_FILE).is_file():
        raise PreparoError(f"{state} não tem versão aprovada; aprove a versão de referência antes")
    shutil.copytree(code, snap_code)
    shutil.copytree(state, snap_state)
    return {"servidor": name, "codigo": str(snap_code), "estado": str(snap_state)}


def restore(config, prefix):
    name, code, state = server_for(config, prefix)
    snap_code, snap_state = snapshot_dirs(config, name)
    replace_dir(snap_code, code)
    replace_dir(snap_state, state)
    return name, code


def draw_order(config, seed):
    rows = [
        {"ordem": 0, "versao": f"{prefix}{number}", "repeticao": repetition}
        for prefix in config["servidores"]
        for number in range(1, VERSIONS_PER_SERVER + 1)
        for repetition in ("R1", "R2")
    ]
    random.Random(seed).shuffle(rows)
    for position, row in enumerate(rows, 1):
        row["ordem"] = position
    target = Path(config["evidencias"]) / "ordem_sorteada.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("ordem", "versao", "repeticao"))
        writer.writeheader()
        writer.writerows(rows)
    target.with_suffix(".meta.json").write_text(json.dumps({
        "semente": seed, "revisoes": len(rows), "csv_sha256": sha256(target),
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"semente": seed, "revisoes": len(rows), "arquivo": str(target)}


def prepare(config, version, repetition):
    prefix = version[0].upper()
    patch = Path(config["patches"]) / f"{version}.patch"
    if not patch.is_file():
        raise PreparoError(f"patch ausente: {patch}")
    if b"\r\n" in patch.read_bytes():
        raise PreparoError("patch deve usar LF; corrija seus finais de linha antes de preparar")
    name, code = restore(config, prefix)
    # Applying LF patches must not inherit Windows' global autocrlf=true.
    # This changes this subprocess only, never the user's Git configuration.
    command = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
               "apply", "--whitespace=nowarn"]
    patch_dir = config["servidores"][prefix].get("diretorio_patch")
    if patch_dir:
        command.append(f"--directory={patch_dir}")
    result = subprocess.run([*command, str(patch)], cwd=code, capture_output=True, text=True)
    if result.returncode != 0:
        restore(config, prefix)
        raise PreparoError(f"patch não aplicou; código e estado restaurados: {result.stderr.strip()}")
    now = datetime.now()
    run_id = f"{version}-{repetition}-{now:%Y%m%d-%H%M%S}"
    evidence = Path(config["evidencias"]) / run_id
    evidence.mkdir(parents=True)
    record = {
        "id": run_id, "servidor": name, "versao": version, "repeticao": repetition,
        "preparado_em": now.isoformat(timespec="seconds"), "patch_sha256": sha256(patch),
        "ambiente": config.get("ambiente", {}),
    }
    (evidence / "ficha.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    registry = Path(config["registro"])
    new_file = not registry.exists()
    registry.parent.mkdir(parents=True, exist_ok=True)
    with registry.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REGISTRY_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({field: record.get(field, "") for field in REGISTRY_FIELDS} | {"evidencias": str(evidence)})
    return record | {"evidencias": str(evidence)}


def collect(config, run_id):
    evidence = Path(config["evidencias"]) / run_id
    record = json.loads((evidence / "ficha.json").read_text(encoding="utf-8"))
    _, _, state = server_for(config, record["versao"][0].upper())
    copied = []
    for folder in STATE_DIRS_TO_COLLECT:
        source = state / folder
        if source.is_dir():
            shutil.copytree(source, evidence / "estado-sentry" / folder, dirs_exist_ok=True)
            copied.append(folder)
    return {"id": run_id, "copiado": copied}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Preparação das revisões do Teste do MCP Sentry")
    parser.add_argument("--config", required=True, type=Path)
    commands = parser.add_subparsers(dest="comando", required=True)
    commands.add_parser("fotografar").add_argument("--servidor", required=True, help="F, G ou D")
    commands.add_parser("restaurar").add_argument("--servidor", required=True, help="F, G ou D")
    commands.add_parser("sortear").add_argument("--semente", required=True, type=int)
    prepare_parser = commands.add_parser("preparar")
    prepare_parser.add_argument("--versao", required=True, help="por exemplo G1")
    prepare_parser.add_argument("--repeticao", required=True, choices=("R1", "R2", "R3"))
    commands.add_parser("coletar").add_argument("--id", required=True)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.comando == "fotografar":
            result = snapshot(config, args.servidor.upper())
        elif args.comando == "restaurar":
            name, _ = restore(config, args.servidor.upper())
            result = {"servidor": name, "status": "restaurado"}
        elif args.comando == "sortear":
            result = draw_order(config, args.semente)
        elif args.comando == "preparar":
            result = prepare(config, args.versao.upper(), args.repeticao)
        else:
            result = collect(config, args.id)
    except (OSError, ValueError, PreparoError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
