"""Record installed baseline sources and static tool signatures; no MCP execution."""
import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    git_root = root / "instalacoes/git/Lib/site-packages/mcp_server_git"
    fs_root = root / "instalacoes/filesystem/node_modules/@modelcontextprotocol/server-filesystem"
    donna_root = root / "codigo/donna"
    git_ast = ast.parse((git_root / "server.py").read_text(encoding="utf-8"))
    enum = next(n for n in git_ast.body if isinstance(n, ast.ClassDef) and n.name == "GitTools")
    git_tools = {n.targets[0].id: ast.literal_eval(n.value) for n in enum.body
                 if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)}
    git_models = {n.name: {a.target.id: ast.unparse(a.annotation) for a in n.body
                          if isinstance(a, ast.AnnAssign)}
                  for n in git_ast.body if isinstance(n, ast.ClassDef) and n.name.startswith("Git")}
    fs_tools = re.findall(r'server\.registerTool\("([^\"]+)"', (fs_root / "dist/index.js").read_text())
    donna_ast = ast.parse((donna_root / "donna_mcp/server.py").read_text(encoding="utf-8"))
    donna_tools = {n.name: {a.arg: ast.unparse(a.annotation) if a.annotation else None
                           for a in n.args.args} for n in donna_ast.body
                   if isinstance(n, ast.FunctionDef) and any(isinstance(d, ast.Call)
                       and isinstance(d.func, ast.Attribute) and d.func.attr == "tool"
                       for d in n.decorator_list)}
    expected = {"F": {"list_directory", "get_file_info", "search_files", "read_multiple_files", "write_file", "create_directory"},
                "G": {"git_log", "git_branch", "git_show", "git_diff", "git_commit"},
                "D": {"ler_email", "consultar_agenda", "remarcar_evento", "enviar_email"}}
    actual = {"F": set(fs_tools), "G": set(git_tools.values()), "D": set(donna_tools)}
    assert all(expected[k] <= actual[k] for k in expected)
    files = {}
    for label, folder in (("git", git_root), ("filesystem", fs_root), ("donna", donna_root)):
        files[label] = {p.relative_to(folder).as_posix(): sha(p) for p in sorted(folder.rglob("*"))
                        if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".js", ".json"}}
    versions = {}
    for name in ("sentry", "git", "donna"):
        python = root / "instalacoes" / name / "Scripts/python.exe"
        versions[name] = subprocess.check_output([python, "-c", "import sys; print(sys.version)"], text=True).strip()
    record = {"inspection": "static_source_only_no_MCP_launch", "git_tools": git_tools,
              "git_input_models": git_models, "filesystem_tools": fs_tools,
              "filesystem_version": json.loads((fs_root / "package.json").read_text())["version"],
              "donna_tools": donna_tools, "required_tools_present": True,
              "python_versions": versions, "source_sha256": files,
              "locks_sha256": {p.name: sha(p) for p in sorted((root / "operador/locks").iterdir()) if p.is_file()}}
    target = root / "evidencias/preparacao/inventario.json"
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"arquivo": str(target), "tools": {k: len(v) for k, v in actual.items()},
                      "required_tools_present": True, "live_catalog": "pendente_DESCOBRIR_operador"}, indent=2))


if __name__ == "__main__":
    main()
