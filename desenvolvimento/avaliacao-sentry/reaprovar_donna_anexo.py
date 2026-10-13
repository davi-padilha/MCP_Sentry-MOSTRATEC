"""Operador aprova a correção mínima e arquiva a referência Donna anterior."""
import json
import sys
from datetime import datetime
from pathlib import Path

from mcp_sentry_gateway.core import approve, capture, canon, digest, inspect
from mcp_sentry_gateway.onboarding import doctor
import preparar_revisao


def main():
    root = Path(r"C:\MCP-Sentry-Mostratec").resolve()
    manifest = root / "config/manifest-donna.json"
    state = root / "estado/donna"
    photo = root / "operador/fotografias/donna_teste"
    verification = json.loads((root / "evidencias/preparacao/verificacao-correcao-anexo.json").read_text(encoding="utf-8"))
    current = capture(manifest)
    shown_hash = digest(canon(current))
    report = inspect(manifest, state)
    changes = report["dossier"]["changes"]
    if len(changes) != 1 or changes[0]["path"] != "donna_mcp/providers/google.py":
        raise RuntimeError("Mudanças diferem da correção mínima preparada; conferir antes de aprovar")
    changed_file = next(f for f in current["files"] if f["path"] == changes[0]["path"])
    if changed_file["sha256"] != verification["provider_sha256"]:
        raise RuntimeError("Fonte mudou desde a verificação do anexo")
    print(json.dumps({"hash": shown_hash, "changes": changes,
                      "verificacao": verification}, indent=2, ensure_ascii=False))
    print("Feche o Codex antes de executar este script. A referência anterior será arquivada.")
    if input("Confira o diff. Digite APROVAR para aprovar esta nova referência: ") != "APROVAR":
        print("Cancelado. Nenhuma aprovação realizada."); return
    if digest(canon(capture(manifest))) != shown_hash:
        raise RuntimeError("Arquivos mudaram; nada aprovado")
    archive = root / "operador/arquivos-historicos" / ("donna-antes-anexo-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    for path in (state, photo, archive):
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise RuntimeError("Caminho inesperado; nada movido")
    if not state.is_dir() or not photo.is_dir():
        raise RuntimeError("Referência anterior incompleta; nada movido")
    archive.mkdir(parents=True, exist_ok=False)
    state.rename(archive / "estado")
    photo.rename(archive / "fotografia")
    state.mkdir()
    result = approve(manifest, state, expected_hash=shown_hash)
    print(json.dumps(result, indent=2))
    config = preparar_revisao.load_config(root / "operador/config.json")
    print(json.dumps(preparar_revisao.snapshot(config, "D"), indent=2))
    diagnosis = doctor(manifest, state)
    record = {"aprovacao": result, "doctor": diagnosis, "arquivo_anterior": str(archive),
              "aprovado_em": datetime.now().astimezone().isoformat()}
    (root / "evidencias/preparacao/referencia-donna-correcao-anexo.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(record, indent=2, ensure_ascii=False))
    if diagnosis["status"] != "ready":
        raise RuntimeError("Doctor exige atenção; preserve a saída")


if __name__ == "__main__":
    main()
