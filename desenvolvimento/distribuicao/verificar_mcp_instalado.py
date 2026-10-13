"""Exercise the installed gateway over stdio using a fictional local MCP only."""
from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

from mcp_sentry_gateway import __version__

ENV = {**os.environ, 'PYTHONIOENCODING':'utf-8', 'PYTHONDONTWRITEBYTECODE':'1'}

SERVER = '''import json, sys
from pathlib import Path
Path(MARKER).write_text('started', encoding='utf-8')
for line in sys.stdin:
    request = json.loads(line)
    method = request.get('method')
    if method == 'initialize':
        result = {'protocolVersion':'2025-06-18','capabilities':{'tools':{}},'serverInfo':{'name':'fictional-echo','version':'1'}}
    elif method == 'notifications/initialized':
        continue
    elif method == 'tools/list':
        result = {'tools':[{'name':'echo','description':'Echo a value','inputSchema':{'type':'object','properties':{'value':{'type':'string'}},'required':['value']}}]}
    elif method == 'tools/call':
        result = {'content':[{'type':'text','text':request['params']['arguments']['value']}]}
    else:
        result = {'isError':True,'content':[{'type':'text','text':'unsupported'}]}
    if 'id' in request:
        print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':result}), flush=True)
'''


def prepare(root):
    root.mkdir(parents=True, exist_ok=True)
    project = root / 'servidor ficticio'
    project.mkdir()
    marker = root / 'backend-iniciado.txt'
    server = project / 'server.py'
    server.write_text(f'MARKER = {str(marker)!r}\n' + SERVER, encoding='utf-8')
    manifest = root / 'manifest.json'
    tool = {'name':'echo', 'description':'Echo a value', 'inputSchema':{'type':'object','properties':{'value':{'type':'string'}},'required':['value']}}
    manifest.write_text(json.dumps({'manifest_version':1,'project_root':str(project),'inspect_roots':['server.py'],
                                   'metadata':{'tools':[tool]}, 'configuration':{'command':[sys.executable,'server.py'],'cwd':'.'}}), encoding='utf-8')
    cli = Path(sys.executable).parent / 'mcp-sentry.exe'
    subprocess.run([str(cli),'approve','--manifest',str(manifest),'--store',str(root / 'estado')],
                   check=True, capture_output=True, timeout=30, env=ENV)
    return manifest, root / 'estado', server, marker


class Client:
    def __init__(self, manifest, store, interface):
        self.stderr = (manifest.parent / f'{interface}-stderr.txt').open('a', encoding='utf-8')
        self.process = subprocess.Popen([sys.executable,'-I','-X','utf8','-m','mcp_sentry_gateway.gateway','--manifest',str(manifest),
                                         '--store',str(store),'--interface',interface], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.stderr, text=True, encoding='utf-8', bufsize=1, env=ENV)
        self.messages = queue.Queue()
        self.reader = threading.Thread(target=self.read, daemon=True)
        self.reader.start()
        self.number = 0
        result = self.call('initialize', {'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'release-validation','version':'1'}})
        assert result['serverInfo']['version'] == __version__
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'}) + '\n')
        self.process.stdin.flush()

    def read(self):
        try:
            for line in self.process.stdout:
                self.messages.put(json.loads(line))
        except Exception as exc:
            self.messages.put(exc)
        finally:
            self.messages.put(None)

    def call(self, method, params=None):
        self.number += 1
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.number,'method':method,'params':params or {}}) + '\n')
        self.process.stdin.flush()
        while True:
            response = self.messages.get(timeout=30)
            if response is None or isinstance(response, Exception):
                raise RuntimeError(f'Gateway ended unexpectedly: {response}')
            if response.get('id') == self.number:
                assert 'error' not in response, response
                return response['result']

    def tool(self, name, arguments=None):
        return self.call('tools/call', {'name':name,'arguments':arguments or {}})

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
        self.reader.join(timeout=5)
        self.process.stdout.close()
        self.stderr.close()
        assert self.process.returncode == 0, self.process.returncode


def exercise(root, existing=False):
    if existing:
        manifest, store, server, marker = root/'manifest.json', root/'estado', root/'servidor ficticio/server.py', root/'backend-iniciado.txt'
    else:
        manifest, store, server, marker = prepare(root)
    with Client(manifest, store, 'execution') as client:
        tools = client.call('tools/list')['tools']
        assert [t['name'] for t in tools] == ['echo']
        assert client.tool('echo', {'value':'native response'})['content'][0]['text'] == 'native response'
    assert marker.exists()
    marker.unlink()
    original = server.read_text('utf-8')
    server.write_text(original + '\n# fictional controlled update\n', encoding='utf-8')
    with Client(manifest, store, 'execution') as client:
        assert client.tool('echo', {'value':'must not run'})['structuredContent']['status'] == 'security_review_required'
    assert not marker.exists(), 'Changed backend started before review'
    with Client(manifest, store, 'review') as client:
        names = [t['name'] for t in client.call('tools/list')['tools']]
        assert 'echo' not in names and 'sentry_authorize_once' not in names
        evidence = client.tool('sentry_review_current_block')['structuredContent']
        invalid = client.tool('sentry_record_assessment', {'decision':'allow','justification':'Fixture','risks':[]})
        assert invalid['isError'] and invalid['structuredContent']['code'] == 'ASSESSMENT_FIELDS_MISSING'
        result = client.tool('sentry_record_assessment', {'review_token':evidence['review_token'],'decision':'allow',
                                                         'justification':'Fictional update for package validation','risks':[]})
        receipt = result['structuredContent']['receipt']
        assert receipt['persisted'] and not receipt['execution_authorized']
        record = json.loads((store/'revisoes-de-atualizacoes'/f"{receipt['review_id']}.json").read_text('utf-8'))
        assert record['verdict']['decision'] == receipt['decision'] == 'allow'
    assert not marker.exists(), 'Review started backend'
    with Client(manifest, store, 'execution') as client:
        blocked = client.tool('echo', {'value':'still blocked'})
        assert blocked['structuredContent']['status'] == 'security_blocked'
        assert blocked['structuredContent']['action_executed'] is False
    assert not marker.exists(), 'Recommendation authorized backend'
    cli = Path(sys.executable).parent / 'mcp-sentry.exe'
    approved = subprocess.run([str(cli),'review-update','--manifest',str(manifest),'--store',str(store),'--action','once'],
                               input='AUTORIZAR\n', text=True, encoding='utf-8', capture_output=True, timeout=30, env=ENV)
    assert approved.returncode == 0, approved.stderr
    with Client(manifest, store, 'execution') as client:
        assert client.tool('echo', {'value':'authorized response'})['content'][0]['text'] == 'authorized response'
    assert marker.exists()
    marker.unlink()
    with Client(manifest, store, 'execution') as client:
        blocked = client.tool('echo', {'value':'no second start'})
        assert blocked['structuredContent']['status'] == 'security_blocked'
        assert blocked['structuredContent']['action_executed'] is False
    assert not marker.exists(), 'One-time permission was reusable'
    return {'native_response_preserved':True,'changed_backend_stayed_stopped':True,'review_separate':True,
            'missing_token_recoverable':True,'receipt_matches_persisted':True,'recommendation_did_not_authorize':True,
            'operator_once_resumed':True,'one_time_permission_consumed':True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--existing', action='store_true')
    args = parser.parse_args()
    if args.prepare_only:
        prepare(args.root)
        print(json.dumps({'version':__version__, 'prepared':True}))
    else:
        print(json.dumps({'version':__version__, 'checks':exercise(args.root, args.existing)}))
