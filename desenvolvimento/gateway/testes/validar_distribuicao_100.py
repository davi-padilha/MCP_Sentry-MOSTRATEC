"""Validate release in a fresh temporary workspace, without the research battery."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO/'desenvolvimento/gateway'
DELIVERY = REPO/'instalar-mcp-sentry'
WHEEL = DELIVERY/'mcp_sentry_gateway-1.0.0-py3-none-any.whl'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(tempfile.mkdtemp(prefix='mcp-sentry-100-validation-'))
    assert target.resolve().parent == Path(tempfile.gettempdir()).resolve()
    resuming = (target/'suite.txt').is_file()
    if not resuming:
        shutil.copytree(SOURCE/'mcp_sentry_gateway', target/'mcp_sentry_gateway',
                        ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(SOURCE/'testes', target/'testes',
                        ignore=shutil.ignore_patterns('__pycache__', 'mcp-sentry-client-test-*'))
    else:
        for path in (SOURCE/'mcp_sentry_gateway').glob('*.py'):
            assert path.read_bytes() == (target/'mcp_sentry_gateway'/path.name).read_bytes()
        for path in (SOURCE/'testes').glob('test_*.py'):
            assert path.read_bytes() == (target/'testes'/path.name).read_bytes()
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'}
    if not resuming:
        suite = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'testes', '-q'],
                               cwd=target, env=env, capture_output=True, text=True, encoding='utf-8')
        (target/'suite.txt').write_text(suite.stdout+'\n'+suite.stderr, encoding='utf-8')
    else:
        suite = subprocess.CompletedProcess([], 0, '', (target/'suite.txt').read_text(encoding='utf-8'))
        assert 'OK (skipped=1)' in suite.stderr and 'FAILED' not in suite.stderr
    assert suite.returncode == 0, 'Suite failed; see '+str(target/'suite.txt')
    modules = []
    with zipfile.ZipFile(WHEEL) as archive:
        for name in archive.namelist():
            if name.startswith('mcp_sentry_gateway/') and name.endswith('.py'):
                assert archive.read(name) == (SOURCE/name).read_bytes(), name
                modules.append(name)
    copied = target/'entrega'
    shutil.copytree(DELIVERY, copied, dirs_exist_ok=True)
    installed = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                '-File', str(copied/'instalar.ps1'), '-PythonExe', sys.executable],
                               env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (target/'instalacao.txt').write_text(installed.stdout+'\n'+installed.stderr, encoding='utf-8')
    assert installed.returncode == 0, 'Installer failed; see '+str(target/'instalacao.txt')
    python = copied/'.venv/Scripts/python.exe'
    for name in modules:
        assert (copied/'.venv/Lib/site-packages'/name).read_bytes() == (SOURCE/name).read_bytes()
    # Upgrade in a separate environment; the delivery installer never reapproves servers.
    subprocess.run([sys.executable, '-m', 'venv', str(target/'upgrade')], env=env, check=True)
    upgrade = target/'upgrade/Scripts/python.exe'
    for wheel in [REPO/'pacote-usuario/mcp_sentry_gateway-0.11.0-py3-none-any.whl', WHEEL]:
        subprocess.run([str(upgrade), '-m', 'pip', 'install', '--no-index', '--no-deps', str(wheel)],
                       env=env, check=True, capture_output=True)
    subprocess.run([str(upgrade), '-c', 'import mcp_sentry_gateway; assert mcp_sentry_gateway.__version__ == "1.0.0"'],
                   env=env, check=True)
    result = {'version':'1.0.0', 'python':sys.version, 'wheel_sha256':sha(WHEEL),
              'source_wheel_installation_modules_equal':len(modules), 'suite_passed':True,
              'suite_tail':suite.stderr.strip().splitlines()[-4:], 'clean_installer_passed':True,
              'upgrade_package_passed':True, 'workspace':str(target), 'installed_python':str(python)}
    (target/'validacao.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
