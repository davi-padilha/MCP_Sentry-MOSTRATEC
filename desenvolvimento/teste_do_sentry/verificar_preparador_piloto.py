"""Verify G1/G2 byte diffs in external scratch copies, without executing MCP."""
import argparse
import ast
import difflib
import json
import shutil
from pathlib import Path

import preparar_revisao as preparador


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--referencia", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if root == Path(root.anchor) or root.exists():
        raise ValueError("Use uma pasta externa nova para esta verificação")
    repo = Path(__file__).resolve().parents[2]
    if root.is_relative_to(repo):
        raise ValueError("Verificação deve ficar fora do repositório")
    original = args.referencia.read_bytes()
    results = []
    for version in ("G1", "G2"):
        lab = root / version
        config = {"servidores": {"G": {"nome": "git-fixture", "codigo": str(lab / "code"),
                                      "estado": str(lab / "state")}},
                  "fotografias": str(lab / "photos"),
                  "patches": str(repo / "desenvolvimento/teste_do_sentry/patches_piloto"),
                  "evidencias": str(lab / "evidence"), "registro": str(lab / "registro.csv"),
                  "ambiente": {"tipo": "verificacao_tecnica_sem_MCP"}}
        source = lab / "code/mcp_server_git/server.py"
        source.parent.mkdir(parents=True)
        source.write_bytes(original)
        (lab / "state").mkdir()
        # Marker used only by the preparation fixture; never a Sentry approval.
        (lab / "state" / preparador.APPROVED_VERSION_FILE).write_text("{}")
        preparador.snapshot(config, "G")
        record = preparador.prepare(config, version, "R1")
        result = source.read_bytes()
        assert b"\r\n" not in result, "Conversão CRLF inesperada"
        ast.parse(result.decode("utf-8"))
        diff = "".join(difflib.unified_diff(original.decode().splitlines(True),
                                          result.decode().splitlines(True),
                                          fromfile="referencia", tofile=version))
        (lab / "diff.txt").write_text(diff, encoding="utf-8")
        if version == "G2":
            a, b = ast.parse(original.decode()), ast.parse(result.decode())
            # Description-only change: remove all string literals before comparing structure.
            class NormalizeStrings(ast.NodeTransformer):
                def visit_Constant(self, node):
                    if isinstance(node.value, str): node.value = "<string>"
                    return node
            assert ast.dump(NormalizeStrings().visit(a)) == ast.dump(NormalizeStrings().visit(b))
        for target in (lab / "code", lab / "state"):
            assert target.resolve().is_relative_to(root)
        preparador.restore(config, "G")
        assert source.read_bytes() == original
        results.append({"versao": version, "id_tecnico": record["id"],
                        "patch_sha256": record["patch_sha256"], "crlf": result.count(b"\r\n"),
                        "diff_lines": len(diff.splitlines()), "restauracao_exata": True})
    (root / "resultado.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
