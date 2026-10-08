"""Prepare one isolated 1.0 battery from frozen 0.11 references; no reviews.

Run once per effort. Native code, patches, gold and protocol remain identical.
"""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/MCP-Sentry-Mostratec')
OLD = ROOT/'series/luna-medium-011-20261007'
REPO = Path(__file__).resolve().parents[2]
BUNDLE_PYTHON = Path('C:/Users/davig/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--esforco', choices=['low', 'medium', 'high'], required=True)
    parser.add_argument('--validacao', type=Path, required=True)
    args = parser.parse_args()
    new = ROOT/f'series/luna-{args.esforco}-100-20261007'
    assert new.resolve().parent == (ROOT/'series').resolve() and not new.exists()
    wheel = REPO/'instalar-mcp-sentry/mcp_sentry_gateway-1.0.0-py3-none-any.whl'
    validation = read(args.validacao)
    assert validation['suite_passed'] and validation['clean_installer_passed'] and validation['upgrade_package_passed']
    assert validation['wheel_sha256'] == sha(wheel)
    frozen = read(OLD/'operador/protocolo/congelamento.json')
    assert read(OLD/'operador/analise/auditoria-final.json')['resumo']['primarias'] == 48
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith('mcp_sentry_gateway/') and name.endswith('.py'):
                assert archive.read(name) == (REPO/'desenvolvimento/gateway'/name).read_bytes()
    def relocate(value):
        if isinstance(value, str):
            return value.replace(str(OLD), str(new))
        if isinstance(value, list):
            return [relocate(v) for v in value]
        if isinstance(value, dict):
            return {k: relocate(v) for k, v in value.items()}
        return value
    new.mkdir()
    for folder in ['config', 'codigo', 'estado', 'operador', 'operador/protocolo',
                   'operador/scripts', 'operador/execucoes', 'operador/fotografias']:
        (new/folder).mkdir(exist_ok=True)
    shutil.copytree(OLD/'instalacoes', new/'instalacoes')
    subprocess.run([str(BUNDLE_PYTHON), '-m', 'pip', '--python', str(new/'instalacoes/sentry/Scripts/python.exe'),
                    'install', '--no-index', '--no-deps', str(wheel)], check=True, capture_output=True)
    protocol = new/'operador/protocolo'
    for filename in ['ordem_sorteada.csv', 'pedidos-fixos.json', 'decisao-operador.json']:
        shutil.copy2(OLD/'operador/protocolo'/filename, protocol/filename)
    shutil.copytree(OLD/'operador/protocolo/patches', protocol/'patches')
    scripts = new/'operador/scripts'
    for path in (OLD/'operador/scripts').iterdir():
        if path.suffix not in ('.py', '.js', '.ps1'):
            continue
        text = path.read_text(encoding='utf-8')
        text = text.replace(str(OLD), str(new)).replace(str(OLD).replace('\\','\\\\'), str(new).replace('\\','\\\\'))
        text = text.replace('luna\\-medium\\-011\\-20261007', f'luna\\-{args.esforco}\\-100\\-20261007')
        text = text.replace('luna-medium-011', f'luna-{args.esforco}-100').replace('battery_luna_medium_011', f'battery_luna_{args.esforco}_100')
        text = text.replace("'medium'", repr(args.esforco)).replace('"medium"', json.dumps(args.esforco))
        text = text.replace('Luna medium', 'Luna '+args.esforco).replace('Luna Medium', 'Luna '+args.esforco)
        text = text.replace('evolucao-011.json', 'evolucao-100.json')
        # Archive each fully collected conversation before preparing another state.
        if path.name == 'orquestrar_bateria.js':
            text = text.replace(
                "title:'Tarefa MCP Luna " + args.esforco + " '+String(b.index).padStart(2,'0')",
                "title:'tarefa mcp Luna " + args.esforco + " '+b.index+'.1'")
            marker = "b.completed.push({...result,thread:b.thread});"
            assert marker in text
            text = text.replace(marker, "await tools.mcp__codex_app__set_thread_archived({threadId:b.thread,archived:true});"+marker)
        (scripts/path.name).write_text(text, encoding='utf-8')
    config = relocate(read(OLD/'operador/config.json'))
    config['ambiente'].update(sentry_versao='1.0.0', sentry_wheel_sha256=sha(wheel),
                              config_esforco=args.esforco, nivel_de_raciocinio=args.esforco)
    with zipfile.ZipFile(wheel) as archive:
        modules = {name: hashlib.sha256(archive.read(name)).hexdigest()
                   for name in sorted(archive.namelist())
                   if name.startswith('mcp_sentry_gateway/') and name.endswith('.py')}
    config['ambiente']['sentry_modulos_sha256'] = hashlib.sha256(
        json.dumps(modules, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    config['ambiente']['sentry_modulos_hash_formato'] = 'SHA256 do mapa JSON canonico caminho:SHA256 dos 16 modulos'
    config['ambiente']['modelo_por_conversa'] = f'create_thread model=gpt-6-luna thinking={args.esforco}; confirmar rollout'
    write(new/'operador/config.json', config)
    sys.path.insert(0, str(new/'instalacoes/sentry/Lib/site-packages'))
    from mcp_sentry_gateway.core import approve, capture, canon, digest
    from mcp_sentry_gateway.onboarding import doctor
    from mcp_sentry_gateway import __version__
    assert __version__ == '1.0.0'
    references = []
    for reference in frozen['referencias']:
        name = reference['servidor']; family = name.removesuffix('_teste')
        source = OLD/'operador/fotografias'/name/'codigo'
        for filename, expected in reference['hash_codigo_fonte_por_arquivo'].items():
            assert sha(source/filename) == expected
        code = new/'codigo'/family
        shutil.copytree(source, code)
        manifest = new/'config'/f'manifest-{family}.json'
        original = read(OLD/'config'/manifest.name)
        write(manifest, relocate(original))
        state = new/'estado'/family; state.mkdir()
        snapshot = capture(manifest)
        assert snapshot['manifest']['privacy_policy'] == original['privacy_policy']
        approved = approve(manifest, state, expected_hash=digest(canon(snapshot)))
        result = doctor(manifest, state)
        assert result['status'] == 'ready'
        shutil.copytree(code, new/'operador/fotografias'/name/'codigo')
        shutil.copytree(state, new/'operador/fotografias'/name/'estado')
        references.append({**reference, 'codigo_original_aprovado':str(source),
                           'novo_hash_referencia':approved['integrity_hash'], 'manifest_sha256':sha(manifest),
                           'envelope_sha256':sha(state/'configuracao-de-execucao-aprovada.json'),
                           'doctor':result, 'estado':'referencia_identica_relocalizada_sem_execucao_backend'})
    write(protocol/'referencias-preparadas.json', references)
    with (new/'operador/execucoes/registro.csv').open('w', encoding='utf-8', newline='') as stream:
        csv.writer(stream).writerow(next(csv.reader((OLD/'operador/execucoes/registro.csv').open(encoding='utf-8'))))
    live = Path.home()/'.codex/config.toml'
    shutil.copy2(live, new/'config/codex-antes.bak')
    current_text = live.read_text(encoding='utf-8')
    # Current execution entries must belong to the completed 0.11 series.
    assert str(OLD).replace('\\','\\\\') in current_text
    proposed_text = current_text.replace(str(OLD).replace('\\','\\\\'), str(new).replace('\\','\\\\'))
    current, proposed = tomllib.loads(current_text), tomllib.loads(proposed_text)
    assert not current['memories']['use_memories'] and not current['memories']['generate_memories']
    names = [f'{f}_teste' for f in ['git','filesystem','donna']]
    names += ['mcp_sentry_review_'+n for n in names[:]]
    assert {k:v for k,v in current.items() if k != 'mcp_servers'} == {k:v for k,v in proposed.items() if k != 'mcp_servers'}
    assert {k:v for k,v in current['mcp_servers'].items() if k not in names} == {k:v for k,v in proposed['mcp_servers'].items() if k not in names}
    for name in names:
        assert proposed['mcp_servers'][name] == relocate(current['mcp_servers'][name])
    (new/'config/config-codex-proposto.toml').write_text(proposed_text, encoding='utf-8')
    write(protocol/'instrumentacao.json', {'arquivos_sha256':{p.name:sha(p) for p in sorted(scripts.iterdir()) if p.is_file()}, 'originais_preservados':True})
    prepared = {**frozen, 'estado':'preparado_aguardando_ativacao_autorizada',
                'preparado_em':datetime.now(timezone.utc).isoformat(), 'modelo':'gpt-6-luna', 'esforco':args.esforco,
                'gateway_version':'1.0.0', 'wheel_sha256':sha(wheel), 'referencias':references,
                'config_operador_sha256':sha(new/'operador/config.json'),
                'config_codex_proposta_sha256':sha(new/'config/config-codex-proposto.toml'),
                'instrumentacao_sha256':sha(protocol/'instrumentacao.json'),
                'validacao_sha256':sha(args.validacao), 'correcao':'Registro recuperavel, contexto e orientacao no dossie; arquivamento depois da coleta.',
                'comparacao':'Mesmos casos, gabarito v2, ordem, pedidos e politicas; nova apresentacao da evidencia e gateway 1.0.',
                'origem_congelamento_sha256':sha(OLD/'operador/protocolo/congelamento.json')}
    write(protocol/'congelamento.json', prepared)
    write(protocol/'prontidao.json', {'pronto_para_OK':True, 'congelamento_sha256':sha(protocol/'congelamento.json'),
          'config_proposta_sha256':sha(new/'config/config-codex-proposto.toml'),
          'manifestos':[{'arquivo':str(new/'config'/f'manifest-{f}.json'), 'sha256':sha(new/'config'/f'manifest-{f}.json')} for f in ['git','filesystem','donna']],
          'patches_sha256':{p['versao']:p['sha256'] for p in frozen['patches']},
          'gabarito_atual_sha256':frozen['gabarito_atual_sha256'], 'modelo':'gpt-6-luna', 'esforco':args.esforco,
          'validacao_reutilizada':'110 controles tecnicos, instalacao limpa e upgrade; SDK e leituras nativas em validacao separada',
          'config_global_preservada':True, 'revisoes_IA':0})
    print(json.dumps({'preparada':str(new), 'doctor':{r['servidor']:r['doctor']['status'] for r in references}, 'revisoes':0}))


if __name__ == '__main__':
    main()
