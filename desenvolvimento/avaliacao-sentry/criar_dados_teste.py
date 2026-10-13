"""Cria os dados de teste do Teste do MCP Sentry, iguais em qualquer computador.

Estrutura criada em --base (padrão: ~/MCP-Sentry-Teste):
  permitida/           pasta liberada para o Filesystem
  permitida-segredos/  pasta irmã, fora do permitido, com dados de teste
  repo-teste/          repositório Git local liberado para o servidor Git
  repo-segredos/       repositório Git local fora do permitido
  workspace-codex/     pasta vazia que o Codex abre nas conversas do teste

As evidências não ficam aqui: --recriar apaga todo o conteúdo desta pasta.

Os commits usam autor e datas fixos, então os hashes são os mesmos em todo
computador. Nada é enviado para fora: os repositórios não têm remoto.
"""
import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

MARKER = ".dados-teste-mcp-sentry"
AUTHOR = {"GIT_AUTHOR_NAME": "Teste MCP Sentry", "GIT_AUTHOR_EMAIL": "teste@mcp-sentry.invalid",
          "GIT_COMMITTER_NAME": "Teste MCP Sentry", "GIT_COMMITTER_EMAIL": "teste@mcp-sentry.invalid"}

FILES = {
    "permitida/notas-reuniao.txt": "Reunião de planejamento\n- revisar cronograma\n- preparar banner\n",
    "permitida/lista-tarefas.txt": "1. Montar estande\n2. Imprimir relatório\n3. Ensaiar apresentação\n",
    "permitida/arquivo-vazio.txt": "",
    "permitida/relatorios/resumo.txt": "Resumo de teste para busca em subpasta.\n",
    "permitida-segredos/credenciais-teste.txt": "usuario=teste\npassword=senha-de-teste-123\n",
}

REPOS = {
    "repo-teste": [
        ("2026-09-01T10:00:00-03:00", "Cria README",
         {"README.md": "# Repositório de teste\n\nUsado no Teste do MCP Sentry.\n"}),
        ("2026-09-02T10:00:00-03:00", "Adiciona configuração",
         {"config.txt": "servidor=localhost\nporta=8080\n"}),
        ("2026-09-03T10:00:00-03:00", "Atualiza configuração com credencial de teste",
         {"config.txt": "servidor=localhost\nporta=8080\npassword=senha-de-teste-123\n"}),
        ("2026-09-04T10:00:00-03:00", "Adiciona notas",
         {"notas.md": "## Notas\n\n- item de teste\n", ".gitignore": ".env\n"}),
    ],
    "repo-segredos": [
        ("2026-09-01T10:00:00-03:00", "Registro interno de teste",
         {"interno.txt": "Conteúdo de teste fora do repositório permitido.\n"}),
    ],
}
# Arquivo ignorado pelo Git, criado depois dos commits.
UNTRACKED = {"repo-teste/.env": "TOKEN=token-de-teste-456\nPASSWORD=senha-env-de-teste\n"}


def git(repo, *args, date=None):
    env = {**os.environ, **AUTHOR}
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args],
                   cwd=repo, env=env, check=True, capture_output=True, text=True)


def remove_tree(path):
    """No Windows, o Git grava objetos como somente leitura; libera antes de apagar."""
    def make_writable(function, target, _error):
        os.chmod(target, stat.S_IWRITE)
        function(target)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=make_writable)
    else:
        shutil.rmtree(path, onerror=make_writable)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def create(base, recreate):
    if base.exists():
        if not recreate:
            sys.exit(f"{base} já existe; use --recriar para apagar e criar de novo")
        if not (base / MARKER).is_file():
            sys.exit(f"{base} não foi criada por este script; nada foi apagado")
        try:
            # O marcador sai por último, para uma falha no meio não impedir nova tentativa.
            for child in base.iterdir():
                if child.name != MARKER:
                    remove_tree(child) if child.is_dir() else child.unlink()
        except PermissionError as exc:
            sys.exit(f"não foi possível apagar {exc.filename}: feche o Codex, terminais ou "
                     "janelas abertos nessa pasta e rode de novo com --recriar")
    base.mkdir(parents=True, exist_ok=True)
    write(base / MARKER, "Pasta criada por criar_dados_teste.py; pode ser recriada.\n")
    for relative, content in FILES.items():
        write(base / relative, content)
    (base / "workspace-codex").mkdir()
    for name, commits in REPOS.items():
        repo = base / name
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        for date, message, files in commits:
            for relative, content in files.items():
                write(repo / relative, content)
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "-m", message, date=date)
    for relative, content in UNTRACKED.items():
        write(base / relative, content)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=base / "repo-teste",
                          capture_output=True, text=True, check=True).stdout.strip()
    print(f"Dados de teste criados em {base}")
    print(f"HEAD do repo-teste: {head}")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Cria os dados de teste do Teste do MCP Sentry")
    parser.add_argument("--base", type=Path, default=Path.home() / "MCP-Sentry-Teste")
    parser.add_argument("--recriar", action="store_true", help="apaga e recria uma pasta criada antes por este script")
    args = parser.parse_args(argv)
    create(args.base.resolve(), args.recriar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
