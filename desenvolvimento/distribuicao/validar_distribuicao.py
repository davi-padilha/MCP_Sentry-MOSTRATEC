"""Validate source, checksums, installation, upgrade and fictional MCP in isolation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / 'desenvolvimento/gateway'
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PIP_DISABLE_PIP_VERSION_CHECK':'1'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_delivery(folder):
    metadata = json.loads((folder/'arquivos-instalacao/VERSAO.json').read_text('utf-8'))
    expected = {'README.md','INSTALAR.cmd','arquivos-instalacao/instalar.ps1','arquivos-instalacao/VERSAO.json',
                'arquivos-instalacao/'+metadata['wheel'], *('ajuda/'+name for name in
                ('README.md','USO-E-ATUALIZACAO.md','CONFIGURACAO.md','PRIVACIDADE.md','SOLUCAO-DE-PROBLEMAS.md'))}
    seen = set()
    for line in (folder/'arquivos-instalacao/SHA256SUMS.txt').read_text('ascii').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ((?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]+)', line)
        if not match or match[2] in seen:
            raise ValueError('Invalid or repeated checksum entry')
        if not (folder/match[2]).resolve().is_relative_to(folder.resolve()):
            raise ValueError('Checksum path escapes delivery')
        seen.add(match[2])
        if sha(folder/match[2]) != match[1]:
            raise ValueError('Checksum mismatch: ' + match[2])
    if seen != expected or metadata['wheel_sha256'] != sha(folder/'arquivos-instalacao'/metadata['wheel']):
        raise ValueError('Delivery inventory or wheel identity mismatch')
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if actual != expected | {'arquivos-instalacao/SHA256SUMS.txt'}:
        raise ValueError('Unexpected files in delivery')
    with zipfile.ZipFile(folder/'arquivos-instalacao'/metadata['wheel']) as archive:
        modules = {name for name in archive.namelist() if name.startswith('mcp_sentry_gateway/') and name.endswith('.py')}
        expected_modules = {f'mcp_sentry_gateway/{p.name}' for p in (SOURCE/'mcp_sentry_gateway').glob('*.py')}
        if modules != expected_modules:
            raise ValueError('Missing or unexpected wheel modules')
        for name in modules:
            if archive.read(name) != (SOURCE/name).read_bytes():
                raise ValueError('Source/wheel mismatch: ' + name)
    return metadata, len(modules)


def run(command, folder, log, *, input_text=None, success=True, timeout=180, env_overrides=None):
    result = subprocess.run(command if isinstance(command, str) else [str(part) for part in command], cwd=folder, env={**ENV, **(env_overrides or {})}, input=input_text,
                            text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=timeout)
    log.write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    if success and result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); see {log}')
    if not success and not result.returncode:
        raise RuntimeError(f'Expected rejection; see {log}')
    return result


def installer(folder, environment=None, *, python=None, extra=()):
    command = ['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',folder/'arquivos-instalacao/instalar.ps1']
    if environment:
        command += ['-Ambiente',environment]
    if python:
        command += ['-PythonExe',python]
    return command + list(extra)


def validate(delivery, target, *, python_sdk=None):
    metadata, modules = verify_delivery(delivery)
    if target.exists():
        raise ValueError('Use a new validation directory; existing evidence will not be overwritten')
    target.mkdir(parents=True)
    source = target/'fonte'
    source.mkdir()
    shutil.copytree(SOURCE/'mcp_sentry_gateway', source/'mcp_sentry_gateway', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(SOURCE/'testes', source/'testes', ignore=shutil.ignore_patterns('__pycache__','mcp-sentry-*-test-*'))
    print('Conferindo suite do gateway...', flush=True)
    suite = run([sys.executable,'-m','unittest','discover','-s','testes','-q'], source, target/'suite.txt')
    combined = suite.stdout + suite.stderr
    counts = re.search(r'Ran (\d+) tests?', combined)
    skipped = re.search(r'OK \(skipped=(\d+)\)', combined)
    if not counts or not re.search(r'\bOK\b', combined):
        raise ValueError('Could not determine suite outcome')
    # A space in the path exercises Windows argument handling.
    copied = target/'entrega com espacos'
    shutil.copytree(delivery, copied)
    environment = target/'instalacao limpa' / '.venv'
    print('Conferindo instalacao limpa e fluxo MCP...', flush=True)
    installed = run(installer(copied, environment, python=sys.executable, extra=['-SemConfigurar']), target, target/'instalacao.txt')
    if 'instalado e conferido' not in installed.stdout:
        raise ValueError('Installer did not confirm installed version')
    python = environment/'Scripts/python.exe'
    for path in (SOURCE/'mcp_sentry_gateway').glob('*.py'):
        if path.read_bytes() != (environment/'Lib/site-packages/mcp_sentry_gateway'/path.name).read_bytes():
            raise ValueError('Installed source mismatch: ' + path.name)
    helper = HERE/'verificar_mcp_instalado.py'
    transport = run([python,'-I',helper,'--root',target/'mcp'], target, target/'mcp.txt')
    transport_result = json.loads(transport.stdout)
    # Upgrade an installed 1.0.0 at a stable path, preserving actual baseline/config files.
    old_wheel = REPO/'distribuicoes-historicas/mcp_sentry_gateway-1.0.0-py3-none-any.whl'
    if not old_wheel.exists():
        old_wheel = REPO/'instalar-mcp-sentry/mcp_sentry_gateway-1.0.0-py3-none-any.whl'
    upgrade_env = target/'upgrade/.venv'
    run([sys.executable,'-I','-m','venv',upgrade_env], target, target/'upgrade-venv.txt')
    upgrade_python = upgrade_env/'Scripts/python.exe'
    run([upgrade_python,'-I','-m','pip','--isolated','install','--no-index','--no-deps',old_wheel], target, target/'upgrade-anterior.txt')
    fixture = target/'upgrade/mcp'
    run([upgrade_python,'-I',helper,'--root',fixture,'--prepare-only'], target, target/'upgrade-preparo.txt')
    preserved = {p:sha(p) for p in fixture.rglob('*.json')}
    config = fixture/'config.toml'
    config.write_text('model = "fictional-model"\n', encoding='utf-8')
    before = config.read_bytes()
    run(installer(copied, upgrade_env, extra=['-SemConfigurar']), target, target/'upgrade.txt')
    if config.read_bytes() != before or any(sha(p) != digest for p,digest in preserved.items()):
        raise ValueError('Upgrade changed protected state or configuration')
    upgrade = run([upgrade_python,'-I',helper,'--root',fixture,'--existing'], target, target/'upgrade-mcp.txt')
    if json.loads(upgrade.stdout)['version'] != metadata['versao']:
        raise ValueError('Upgrade did not install expected version')
    # Automatic Python discovery must work despite unusable WindowsApps aliases.
    automatic_env = target/'automatico/.venv'
    automatic = run(installer(copied, automatic_env, extra=['-SemConfigurar']), target, target/'python-automatico.txt')
    auto_version = run([automatic_env/'Scripts/python.exe','-I','-c','import sys; print(sys.version.split()[0])'], target, target/'python-automatico-versao.txt').stdout.strip()
    # Tampering is rejected before creating an environment.
    tampered = target/'entrega alterada'
    shutil.copytree(copied, tampered)
    with (tampered/'README.md').open('a', encoding='utf-8') as stream:
        stream.write('\nUnexpected edit\n')
    rejected_env = target/'nao-deve-existir/.venv'
    rejected = run(installer(tampered, rejected_env, python=sys.executable, extra=['-SemConfigurar']), target, target/'hash-rejeitado.txt', success=False)
    if rejected_env.exists() or 'diferente da soma' not in rejected.stderr:
        raise ValueError('Tampered delivery was not rejected before installation')
    invalid_env = target/'python-invalido/.venv'
    invalid = run(installer(copied, invalid_env, python=target/'inexistente/python.exe', extra=['-SemConfigurar']), target, target/'python-rejeitado.txt', success=False)
    if invalid_env.exists() or 'Python informado nao funciona' not in invalid.stderr:
        raise ValueError('Invalid Python did not receive actionable diagnostics')
    existing_env = target/'ambiente incompleto'
    existing_env.mkdir()
    sentinel = existing_env/'preservar.txt'
    sentinel.write_text('existing user data', encoding='utf-8')
    run(installer(copied, existing_env, python=sys.executable, extra=['-SemConfigurar']), target,
        target/'ambiente-incompleto.txt', success=False)
    if list(existing_env.iterdir()) != [sentinel] or sentinel.read_text('utf-8') != 'existing user data':
        raise ValueError('Incomplete existing environment was overwritten')
    # A created venv without the package can be reused after an interrupted install.
    empty_env = target/'ambiente vazio/.venv'
    run([sys.executable,'-I','-m','venv',empty_env], target, target/'ambiente-vazio-preparo.txt')
    run(installer(copied, empty_env, extra=['-SemConfigurar']), target, target/'ambiente-vazio.txt')
    # Test both opening the wizard and its real confirmations on disposable TOML only.
    setup_project = target/'setup/servidor'
    setup_project.mkdir(parents=True)
    setup_server = setup_project/'server.py'
    # Reuse the already validated fictional server; marker is redirected into this fixture.
    server_text = (target/'mcp/servidor ficticio/server.py').read_text('utf-8').split('\n',1)[1]
    setup_server.write_text(f'MARKER = {str(target / "setup/backend.txt")!r}\n' + server_text, encoding='utf-8')
    setup_config = target/'setup/config.toml'
    setup_config.write_text('model = "fictional"\n\n[mcp_servers.example]\ncommand = ' + json.dumps(str(python)) + '\nargs = [' + json.dumps(str(setup_server)) + ']\n', encoding='utf-8')
    setup_state = target/'setup/states'
    configured = run(installer(copied, environment, extra=['-Configurar','-CodexConfig',setup_config,'-StateRoot',setup_state]),
                     target, target/'setup.txt', input_text='1\n\n\nDESCOBRIR\nAPROVAR\nSUBSTITUIR\n')
    config_data = tomllib.loads(setup_config.read_text('utf-8'))
    if 'mcp_sentry_review_example' not in config_data['mcp_servers'] or config_data['model'] != 'fictional':
        raise ValueError('Setup did not connect fictional MCP or changed unrelated options')
    backups = list(setup_config.parent.glob('config.toml.sentry-backup-*.bak'))
    if len(backups) != 1 or not (setup_state/'example/codex-installation.json').is_file():
        raise ValueError('Setup backup/installation receipt missing')
    # Default fresh install asks once; answering no leaves client configuration untouched.
    offered = run(installer(copied, target/'oferta/.venv', python=sys.executable), target, target/'oferta.txt', input_text='n\n')
    if 'Deseja abrir' not in offered.stdout or 'Configuracao nao iniciada' not in offered.stdout:
        raise ValueError('Optional setup offer did not respect refusal')
    # Exercise the double-click entry point with a disposable user profile.
    print('Conferindo duplo clique, pasta fixa e compatibilidade com instalacao anterior...', flush=True)
    launcher_copy = target/'pacote do usuario'
    shutil.copytree(delivery, launcher_copy)
    profile = target/'perfil do usuario'
    launcher_env = {'LOCALAPPDATA':str(profile), 'MCP_SENTRY_NO_PAUSE':'1'}
    cmd = f'cmd.exe /d /s /c ""{launcher_copy / "INSTALAR.cmd"}" -PythonExe "{sys.executable}" -SemConfigurar"'
    run(cmd, target, target/'duplo-clique.txt', env_overrides=launcher_env)
    stable_env = profile/'MCP-Sentry-Gateway/.venv'
    stable_python = stable_env/'Scripts/python.exe'
    installed_help = stable_env.parent/'ajuda-mcp-sentry'
    for path in (launcher_copy/'ajuda').glob('*.md'):
        if path.read_bytes() != (installed_help/path.name).read_bytes():
            raise ValueError('Installed help is missing or different')
    if (installed_help/'VERSAO.json').read_bytes() != (launcher_copy/'arquivos-instalacao/VERSAO.json').read_bytes():
        raise ValueError('Installed version record is missing')
    # The source package path disappears while the executable remains usable.
    moved = target/'pacote guardado apos instalacao'
    if not all(p.resolve().is_relative_to(target.resolve()) for p in (launcher_copy, moved)):
        raise ValueError('Unsafe validation move')
    launcher_copy.rename(moved)
    run([stable_python,'-I',helper,'--root',target/'mcp-sem-pacote'], target, target/'sem-pasta-extraida.txt')
    bad_cmd = f'cmd.exe /d /s /c ""{tampered / "INSTALAR.cmd"}" -SemConfigurar"'
    run(bad_cmd, target, target/'duplo-clique-rejeitado.txt', success=False, env_overrides=launcher_env)
    legacy = target/'pacote anterior'
    shutil.copytree(delivery, legacy)
    legacy_env = legacy/'.venv'
    run([sys.executable,'-I','-m','venv',legacy_env], target, target/'legado-venv.txt')
    legacy_python = legacy_env/'Scripts/python.exe'
    run([legacy_python,'-I','-m','pip','--isolated','install','--no-index','--no-deps',old_wheel], target, target/'legado-anterior.txt')
    run(installer(legacy, extra=['-SemConfigurar']), target, target/'legado-reutilizado.txt', env_overrides=launcher_env)
    legacy_version = run([legacy_python,'-I','-c','import mcp_sentry_gateway; print(mcp_sentry_gateway.__version__)'], target, target/'legado-versao.txt')
    if legacy_version.stdout.strip() != metadata['versao']:
        raise ValueError('Existing package environment was not upgraded in place')
    summary = {'estado':'validada', 'python_suite_instalador':sys.version.split()[0], 'python_deteccao_automatica':auto_version,
               'testes_total':int(counts[1]), 'ignorados':int(skipped[1]) if skipped else 0,
               'modulos_fonte_wheel_instalacao_identicos':modules, 'instalacao_limpa':True, 'upgrade_100_para_110':True,
               'upgrade_preserva_estado_e_configuracao':True, 'deteccao_python':True, 'hash_alterado_rejeitado':True,
               'python_invalido_rejeitado':True, 'setup_opcional_com_backup':True, 'setup_recusado_respeitado':True,
               'ambiente_incompleto_preservado':True, 'ambiente_vazio_reutilizado':True,
               'duplo_clique_e_codigo_de_saida':True, 'instalacao_padrao_em_pasta_fixa':True,
               'funciona_sem_pasta_extraida':True, 'ajuda_preservada_na_instalacao':True,
               'ambiente_legado_reutilizado':True,
               'transporte_mcp_stdio':transport_result['checks']}
    summary['passaram'] = summary['testes_total'] - summary['ignorados']
    if python_sdk:
        run([python_sdk,'-I',HERE/'verificar_sdk.py','--python-installed',python,'--root',target/'sdk'], target, target/'sdk.txt')
        sdk = json.loads((target/'sdk.txt').read_text('utf-8').strip())
        summary['sdk_mcp'] = sdk
    from preparar_distribuicao import source_digest
    result = {'date':datetime.now(ZoneInfo('America/Sao_Paulo')).date().isoformat(), 'summary':summary,
              'wheel_sha256':metadata['wheel_sha256'],'source_digest':source_digest()}
    (target/'validacao.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entrega', type=Path, required=True)
    parser.add_argument('--destino', type=Path, required=True)
    parser.add_argument('--python-sdk', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.entrega.resolve(), args.destino.resolve(), python_sdk=args.python_sdk), ensure_ascii=False, indent=2))
