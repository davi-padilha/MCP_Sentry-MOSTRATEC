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
    print(json.dumps({'python':sys.version.split()[0],'fictional_data_only':True,'interfaces':results}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-installed', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.python_installed, args.root))
