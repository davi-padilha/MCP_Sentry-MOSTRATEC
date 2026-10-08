"""Real SDK schemas and native read controls, using only fictional lab data."""
import argparse
import asyncio
import hashlib
import json
import os
import shutil
import sys
import tempfile
import tomllib
from datetime import timedelta
from pathlib import Path

from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def connect(python, manifest, state, interface, env, action):
    params = StdioServerParameters(command=str(python), args=['-m','mcp_sentry_gateway.gateway',
        '--manifest',str(manifest),'--store',str(state),'--interface',interface], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=180)) as client:
            await client.initialize()
            tools = (await client.list_tools()).tools
            for tool in tools:
                Draft202012Validator.check_schema(tool.inputSchema)
                if tool.outputSchema:
                    Draft202012Validator.check_schema(tool.outputSchema)
            return await action(client, tools)


async def run(series):
    sys.path.insert(0, str(series/'instalacoes/sentry/Lib/site-packages'))
    from mcp_sentry_gateway.core import approve, safe_text
    from mcp_sentry_gateway import __version__
    assert __version__ == '1.0.0'
    python = series/'instalacoes/sentry/Scripts/python.exe'
    target = Path(tempfile.mkdtemp(prefix='mcp-sentry-100-sdk-'))
    live = tomllib.loads((Path.home()/'.codex/config.toml').read_text(encoding='utf-8'))
    results = {}
    native = {
        'git':('git_log',{'repo_path':'C:/MCP-Sentry-Mostratec/dados/repo-teste','max_count':3}),
        'filesystem':('list_directory',{'path':'C:/MCP-Sentry-Mostratec/dados/permitida'}),
        'donna':('consultar_agenda',{'inicio':'2026-10-12T00:00:00-03:00','fim':'2026-10-13T00:00:00-03:00'})}
    for family, (name, args) in native.items():
        state = target/family
        state.mkdir()
        for filename in ['versao-aprovada.json','configuracao-de-execucao-aprovada.json']:
            shutil.copy2(series/'estado'/family/filename, state/filename)
        async def read_native(client, tools, name=name, args=args):
            tool = next(t for t in tools if t.name == name)
            Draft202012Validator(tool.inputSchema).validate(args)
            result = await client.call_tool(name, args)
            assert not result.isError, 'Native call failed: '+name
            payload = result.model_dump(mode='json')
            return {'tools':len(tools), 'native_call':name, 'success':True,
                    'result_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()}
        results[family] = await connect(python, series/'config'/f'manifest-{family}.json', state,
                                        'execution', live['mcp_servers'][family+'_teste'].get('env',{}), read_native)
    # A synthetic changed server tests review schemas without running the update.
    sys.path.insert(0, str(Path(__file__).parent))
    from test_gateway_universal import SERVER_SOURCE
    project = target/'fixture'; project.mkdir()
    (project/'server.py').write_text(SERVER_SOURCE,encoding='utf-8')
    manifest = target/'fixture.json'
    tool = {'name':'echo','description':'Echo a value','inputSchema':{'type':'object','properties':{'value':{'type':'string'}},'required':['value']}}
    manifest.write_text(json.dumps({'manifest_version':1,'project_root':'fixture','inspect_roots':['server.py'],
        'metadata':{'tools':[tool]},'configuration':{'command':[sys.executable,'server.py'],'cwd':'.'}}),encoding='utf-8')
    for decision in ['allow','block']:
        (project/'server.py').write_text(SERVER_SOURCE,encoding='utf-8')
        state = target/decision; state.mkdir(); approve(manifest,state)
        (project/'server.py').write_text(SERVER_SOURCE+'\n# controlled SDK update\n',encoding='utf-8')
        async def review(client, tools, decision=decision, state=state):
            evidence = await client.call_tool('sentry_review_current_block',{})
            assert not evidence.isError
            token = evidence.structuredContent['review_token']
            invalid = await client.call_tool('sentry_record_assessment',{'decision':decision,'justification':'SDK fixture','risks':[]})
            assert invalid.isError and invalid.structuredContent['missing_fields']==['review_token']
            assert invalid.structuredContent['recoverable']
            recorded = await client.call_tool('sentry_record_assessment',{'review_token':token,'decision':decision,'justification':'SDK fixture','risks':[]})
            receipt = recorded.structuredContent['receipt']
            record = json.loads((state/'revisoes-de-atualizacoes'/(receipt['review_id']+'.json')).read_text())
            assert receipt['decision']==record['verdict']['decision']==decision
            assert receipt['persisted'] and not receipt['execution_authorized']
            return {'schemas_valid':True,'missing_token_recoverable':True,'receipt_matches':True,'backend_started':False}
        results['review_'+decision] = await connect(python,manifest,state,'review',{},review)
    result = {'version':'1.0.0','checks':results,'workspace':str(target),'fictitious_data_only':True}
    (target/'validacao-sdk.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serie',type=Path,required=True)
    asyncio.run(run(parser.parse_args().serie))
