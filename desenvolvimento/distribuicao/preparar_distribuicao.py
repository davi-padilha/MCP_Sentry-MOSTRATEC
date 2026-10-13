"""Build, validate and package a local release without changing client configuration."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'desenvolvimento/gateway'
DELIVERY = REPO / 'instalar-mcp-sentry'
HERE = Path(__file__).resolve().parent
DOCS = ('CONFIGURACAO.md', 'PRIVACIDADE.md', 'SOLUCAO-DE-PROBLEMAS.md')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_digest(source=SOURCE):
    digest = hashlib.sha256()
    for path in sorted((source / 'mcp_sentry_gateway').glob('*.py')):
        digest.update(path.name.encode() + b'\0' + path.read_bytes())
    return digest.hexdigest()


def project_identity():
    project = tomllib.loads((SOURCE / 'pyproject.toml').read_text('utf-8'))['project']
    version = project['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Use a final three-part release version.')
    tree = ast.parse((SOURCE / 'mcp_sentry_gateway/__init__.py').read_text('utf-8'))
    declared = next(ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets))
    if declared != version:
        raise ValueError('pyproject.toml and __version__ disagree; no release was published.')
    match = re.fullmatch(r'>=(\d+\.\d+)', project['requires-python'])
    if not match:
        raise ValueError('Review the installer before changing the Python requirement syntax.')
    return version, match[1]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def checksums(folder):
    files = sorted(path for path in folder.iterdir() if path.is_file() and path.name != 'SHA256SUMS.txt')
    (folder / 'SHA256SUMS.txt').write_text(''.join(f'{sha(path)}  {path.name}\n' for path in files), encoding='ascii', newline='\n')


def deterministic_zip(destination, entries):
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def build_wheel(work, version):
    build = work / 'fonte-build'
    build.mkdir()
    for name in ('pyproject.toml', 'README.md', 'setup.cfg'):
        shutil.copy2(SOURCE / name, build / name)
    (build / 'mcp_sentry_gateway').mkdir()
    for path in (SOURCE / 'mcp_sentry_gateway').glob('*.py'):
        shutil.copy2(path, build / 'mcp_sentry_gateway' / path.name)
    result = subprocess.run([sys.executable, '-I', '-c', "from setuptools.build_meta import build_wheel; build_wheel('dist')"],
                            cwd=build, capture_output=True, text=True, encoding='utf-8', errors='replace',
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'}, timeout=120)
    (work / 'build.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'Build failed; see {work / "build.txt"}. Install setuptools>=68 and wheel in the build Python.')
    wheel = build / 'dist' / f'mcp_sentry_gateway-{version}-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as archive:
        entries = [(name, archive.read(name)) for name in archive.namelist()]
        modules = {name for name, _ in entries if name.startswith('mcp_sentry_gateway/') and name.endswith('.py')}
        expected = {f'mcp_sentry_gateway/{p.name}' for p in (SOURCE / 'mcp_sentry_gateway').glob('*.py')}
        if modules != expected:
            raise ValueError('Wheel has missing or extra Python modules.')
        for name in modules:
            if archive.read(name) != (SOURCE / name).read_bytes():
                raise ValueError(f'Source and wheel differ: {name}')
    canonical = work / wheel.name
    deterministic_zip(canonical, entries)
    return canonical


def release(python_sdk=None):
    version, minimum = project_identity()
    work_root = REPO / 'laboratorio/execucoes'
    work_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f'distribuicao-{version}-', dir=work_root))
    wheel = build_wheel(work, version)
    stage = work / 'entrega'
    stage.mkdir()
    shutil.copy2(wheel, stage / wheel.name)
    for name in (*DOCS, 'instalar.ps1'):
        text = (DELIVERY / name).read_text('utf-8').replace('\r\n', '\n')
        (stage / name).write_text(text, encoding='utf-8', newline='\n')
    template = (HERE / 'README_USUARIO.md.in').read_text('utf-8')
    for key, value in {'VERSAO': version, 'PYTHON_MINIMO': minimum, 'WHEEL': wheel.name}.items():
        template = template.replace('{{' + key + '}}', value)
    if '{{' in template:
        raise ValueError('Unresolved README placeholder.')
    (stage / 'README.md').write_text(template, encoding='utf-8', newline='\n')
    metadata = {'versao': version, 'python_minimo': minimum, 'escopo': 'Prototipo Windows; ferramentas MCP locais stdio',
                'wheel': wheel.name, 'wheel_sha256': sha(wheel), 'fonte_modulos_sha256': source_digest(),
                'validacao_tecnica': {'estado': 'em_validacao'},
                'baterias_modelo': {'registro': 'pesquisa/02_resultados/COMPARACAO_LUNA_110.md',
                                   'observacao': 'Campanhas anteriores, independentes da validacao desta distribuicao; wheel reconstruido da mesma fonte funcional.'}}
    write_json(stage / 'VERSAO.json', metadata)
    checksums(stage)
    from validar_distribuicao import validate
    print(f'Validando {version}. Evidencias: {work}', flush=True)
    validation = validate(stage, work / 'validacao', python_sdk=python_sdk)
    metadata['validacao_tecnica'] = validation['summary']
    metadata['data_validacao'] = validation['date']
    write_json(stage / 'VERSAO.json', metadata)
    checksums(stage)
    # Validate the final metadata/checksum bytes too; do not rerun the installation.
    from validar_distribuicao import verify_delivery
    verify_delivery(stage)
    output = REPO / 'distribuicoes'
    output.mkdir(exist_ok=True)
    staged_zip = work / f'mcp-sentry-{version}.zip'
    deterministic_zip(staged_zip, [(f'instalar-mcp-sentry/{p.name}', p.read_bytes()) for p in stage.iterdir()])
    # Archive prior wheels before replacing the delivery; preserve any local .venv.
    for old in DELIVERY.glob('*.whl'):
        if old.name == wheel.name:
            continue
        archived = REPO / 'pacote-usuario' / old.name
        if archived.exists() and sha(archived) != sha(old):
            raise ValueError(f'Historical wheel conflict: {archived}')
        if not archived.exists():
            shutil.copy2(old, archived)
    for path in stage.iterdir():
        shutil.copy2(path, DELIVERY / path.name)
    for old in DELIVERY.glob('*.whl'):
        if old.name != wheel.name:
            # Only specific archived wheel files inside DELIVERY are removed.
            if old.parent.resolve() != DELIVERY.resolve() or sha(old) != sha(REPO / 'pacote-usuario' / old.name):
                raise ValueError('Archive verification failed.')
            old.unlink()
    final_zip = output / staged_zip.name
    shutil.copy2(staged_zip, final_zip)
    (output / 'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(output.glob('*.zip'))), encoding='ascii', newline='\n')
    print(json.dumps({'version': version, 'zip': str(final_zip), 'zip_sha256': sha(final_zip), 'evidence': str(work),
                      'validation': validation['summary']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-sdk', type=Path, help='Optional Python with mcp and jsonschema for official SDK validation')
    args = parser.parse_args()
    try:
        release(args.python_sdk)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'Distribuicao nao publicada: {exc}', file=sys.stderr)
        sys.exit(1)
