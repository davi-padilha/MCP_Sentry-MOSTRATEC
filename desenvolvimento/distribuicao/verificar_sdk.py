"""Official SDK schema and transport checks against an isolated fictional MCP."""
import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(python, root):
    helper = Path(__file__).with_name('verificar_mcp_instalado.py')
    subprocess.run([str(python),'-I',str(helper),'--root',str(root),'--prepare-only'], check=True,
                   capture_output=True, env={**os.environ,'PYTHONIOENCODING':'utf-8'}, timeout=30)
    results = {}
    for interface in ('execution','review'):
        parameters = StdioServerParameters(command=str(python), args=['-I','-X','utf8','-m','mcp_sentry_gateway.gateway',
            '--interface',interface,'--manifest',str(root/'manifest.json'),'--store',str(root/'estado')],
            env={'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'})
        async with stdio_client(parameters) as (read,write):
            async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=30)) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                for tool in tools:
                    Draft202012Validator.check_schema(tool.inputSchema)
                    if tool.outputSchema:
                        Draft202012Validator.check_schema(tool.outputSchema)
                if interface == 'execution':
                    assert [t.name for t in tools] == ['echo']
                    response = await session.call_tool('echo', {'value':'SDK native response'})
                    assert not response.isError and response.content[0].text == 'SDK native response'
                else:
                    status = await session.call_tool('sentry_security_status', {})
                    assert status.structuredContent['review_offer']['requires_user_request']
                    assert status.structuredContent['review_offer']['tool'] == 'sentry_review_current_block'
                    status_tool = next(t for t in tools if t.name == 'sentry_security_status')
                    Draft202012Validator(status_tool.outputSchema).validate(status.structuredContent)
                    evidence = await session.call_tool('sentry_review_current_block', {})
                    assert not evidence.isError
                    registered = await session.call_tool('sentry_record_assessment', {
                        'review_token':evidence.structuredContent['review_token'],'decision':'block',
                        'justification':'Fictional SDK validation','risks':[]})
                    assert not registered.isError
                    assert registered.structuredContent['receipt']['persisted']
                    assert not registered.structuredContent['receipt']['execution_authorized']
                results[interface] = {'tools':len(tools),'schemas_valid':True,'call_succeeded':True}
        if interface == 'execution':
            server = root/'servidor ficticio/server.py'
            server.write_text(server.read_text('utf-8')+'\n# SDK fictional update\n', encoding='utf-8')
    permanent = root/'permanent'
    subprocess.run([str(python),'-I',str(helper),'--root',str(permanent),'--prepare-only'], check=True,
                   capture_output=True, env={**os.environ,'PYTHONIOENCODING':'utf-8'}, timeout=30)
    server = permanent/'servidor ficticio/server.py'
    server.write_text(server.read_text('utf-8')+'\n# reviewed permanent update\n', encoding='utf-8')
    def parameters(interface):
        return StdioServerParameters(command=str(python), args=['-I','-X','utf8','-m','mcp_sentry_gateway.gateway',
            '--conversation-approval','--interface',interface,'--manifest',str(permanent/'manifest.json'),
            '--store',str(permanent/'estado')], env={'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'})
    async with stdio_client(parameters('review')) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            assert len(tools) == 6
            for tool in tools:
                Draft202012Validator.check_schema(tool.inputSchema)
                Draft202012Validator.check_schema(tool.outputSchema)
            accept_tool = next(t for t in tools if t.name == 'sentry_accept_version')
            evidence = (await session.call_tool('sentry_review_current_block', {})).structuredContent
            recorded = await session.call_tool('sentry_record_assessment', {
                'review_token':evidence['review_token'],'decision':'allow',
                'justification':'SDK technical fixture, not a model assessment','risks':[]})
            assert recorded.structuredContent['approval_scope_required']
            accepted = await session.call_tool('sentry_accept_version', {
                'review_id':evidence['review_id'],'reviewed_hash':evidence['current_hash'],
                'dossier_hash':evidence['dossier_hash'],
                'confirmation':accept_tool.inputSchema['properties']['confirmation']['const']})
            assert not accepted.isError and accepted.structuredContent['status'] == 'version_accepted'
            Draft202012Validator(accept_tool.outputSchema).validate(accepted.structuredContent)
    for values in (['first','second'], ['reconnected']):
        async with stdio_client(parameters('execution')) as (read,write):
            async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=30)) as session:
                await session.initialize()
                for value in values:
                    response = await session.call_tool('echo', {'value':value})
                    assert not response.isError and response.content[0].text == value
    server.write_text(server.read_text('utf-8')+'\n# unapproved subsequent change\n', encoding='utf-8')
    async with stdio_client(parameters('execution')) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=30)) as session:
            await session.initialize()
            blocked = await session.call_tool('echo', {'value':'must not run'})
            assert blocked.structuredContent['status'] == 'security_review_required'
            assert blocked.structuredContent['review_offer']['requires_user_request']
    lifecycle = json.loads((permanent/'estado/relatorios-de-seguranca/backend-lifecycle-current.json').read_text('utf-8'))
    assert lifecycle['spawn_attempts'] == 0
    results['permanent_acceptance'] = {'schemas_valid':True,'repeated_calls':True,'reconnection':True,
                                      'later_change_blocked_before_spawn':True,'requires_distinct_confirmation':True}
    results['review_offer'] = {'schema_valid':True,'requires_separate_user_request':True,
                              'read_only_tool_identified':True,'available_after_new_block':True}
    print(json.dumps({'python':sys.version.split()[0],'fictional_data_only':True,'interfaces':results}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-installed', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.python_installed, args.root))
