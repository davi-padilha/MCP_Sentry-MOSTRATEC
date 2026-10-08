"""Bateria portatil: nao inicia conversas nem executa variantes."""
import argparse,csv,hashlib,json,shutil,subprocess,sys,zipfile
from pathlib import Path
import preparar_revisao as harness
PACKAGE=Path(__file__).resolve().parents[1]
FAMILIES={'G':'git','F':'filesystem','D':'donna'}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(args,**kw):subprocess.run([str(a) for a in args],check=True,**kw)
def python(root,f):return root/'instalacoes'/f/'Scripts/python.exe'
def cli(root,name):return root/'instalacoes/sentry/Scripts'/name
def rows():return list(csv.DictReader((PACKAGE/'operador/ordem_sorteada.csv').open(encoding='utf-8-sig',newline='')))
def verify():
 hashes=read(PACKAGE/'SHA256.json')
 for name,digest in hashes.items():
  assert hashlib.sha256((PACKAGE/name).read_bytes()).hexdigest()==digest, name
 order=rows();assert len(order)==48
 assert {(r['versao'],r['repeticao']) for r in order}=={(f'{p}{n}',r) for p in FAMILIES for n in range(1,9) for r in ('R1','R2')}
 print('Integridade OK: 24 variantes, 48 execucoes, arquivos conferidos.')
def safe(root):
 assert root.is_absolute() and root!=PACKAGE and PACKAGE not in root.parents and root not in PACKAGE.parents
 assert (root/'.bateria-sentry-portatil').is_file(), 'Runtime nao inicializado por este pacote'
 config=read(root/'operador/config.json')
 for s in config['servidores'].values():
  for k in ['codigo','estado']:assert Path(s[k]).resolve().is_relative_to(root)
 assert Path(config['fotografias']).resolve().is_relative_to(root)
 return config
def init(root,effort,install):
 verify();assert not root.exists(),'Use uma pasta nova, fora do repo.'
 assert root.is_absolute() and root!=PACKAGE and PACKAGE not in root.parents and root not in PACKAGE.parents
 root.mkdir(parents=True);(root/'.bateria-sentry-portatil').touch()
 for folder in ['dados','workspace-revisor','credenciais/donna','operador/evidencias','config']: (root/folder).mkdir(parents=True,exist_ok=True)
 config={'servidores':{},'fotografias':str(root/'operador/fotografias'),'patches':str(PACKAGE/'operador/patches'),'evidencias':str(root/'operador/evidencias'),'registro':str(root/'operador/registro.csv'),'ambiente':{'modelo':'gpt-6-luna','esforco':effort,'sentry':'1.0.0','politica':'mcp-sentry-review-v2'}}
 fragments=[]
 for prefix,f in FAMILIES.items():
  code=root/'codigo'/f;code.mkdir(parents=True)
  with zipfile.ZipFile(PACKAGE/'referencias'/f'{f}.zip') as z:
   assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
   z.extractall(code)
  state=root/'estado'/f;state.mkdir(parents=True)
  config['servidores'][prefix]={'nome':f'{f}_teste','codigo':str(code),'estado':str(state),'diretorio_patch':'.'}
  m=read(PACKAGE/'manifestos'/f'{f}.json');m['project_root']=str(code)
  m['configuration']['command']=[x.replace('@PYTHON@',str(python(root,f))).replace('@NODE@',shutil.which('node') or 'node').replace('@DADOS@',str(root/'dados')) for x in m['configuration']['command']]
  write(root/'config'/f'manifest-{f}.json',m)
  if install and f!='filesystem':
   run([sys.executable,'-m','venv',root/'instalacoes'/f]);run([python(root,f),'-m','pip','install','-r',PACKAGE/'dependencias'/f'{f}.txt'])
  for interface,name in [('execution',f'{f}_teste'),('review',f'mcp_sentry_review_{f}_teste')]:
   args=['--interface',interface,'--manifest',str(root/'config'/f'manifest-{f}.json'),'--store',str(state)]
   fragments.append(f'[mcp_servers.{name}]\ncommand = {json.dumps(str(cli(root,"mcp-sentry-gateway.exe")))}\nargs = {json.dumps(args)}\n')
 for f in ['repo-teste','repo-segredos']:
  run(['git','clone','--quiet',PACKAGE/'dados'/f'{f}.bundle',root/'dados'/f])
  shutil.copy2(PACKAGE/'dados'/f'{f}.env-ficticio',root/'dados'/f/'.env')
 for f in ['permitida','permitida-segredos']:shutil.copytree(PACKAGE/'dados'/f,root/'dados'/f)
 if install:
  run([sys.executable,'-m','venv',root/'instalacoes/sentry']);run([python(root,'sentry'),'-m','pip','install','-r',PACKAGE/'dependencias/sentry.txt']);run([python(root,'sentry'),'-m','pip','install','--no-deps',PACKAGE/'dependencias/mcp_sentry_gateway-1.0.0-py3-none-any.whl'])
 write(root/'operador/config.json',config)
 prompts=read(PACKAGE/'operador/pedidos-fixos.json')
 for p in ['G','F']:prompts['tarefas'][p]=prompts['tarefas'][p].replace('C:\\MCP-Sentry-Mostratec\\dados',str(root/'dados'))
 write(root/'operador/pedidos-fixos.json',prompts)
 shutil.copy2(PACKAGE/'operador/ordem_sorteada.csv',root/'operador/ordem_sorteada.csv')
 for i,fragment in enumerate(fragments):
  if 'donna_teste]' in fragment:
   env={name:str(root/path) for name,path in {'MCP_SECRETARY_CREDENTIALS_FILE':'credenciais/donna/credentials.json','MCP_SECRETARY_TOKEN_FILE':'credenciais/donna/token.json','MCP_SECRETARY_AUDIT_FILE':'operador/donna-audit.jsonl','MCP_SECRETARY_MUTATION_STORE_FILE':'operador/donna-mutacoes.json'}.items()}
   fragments[i]=fragment+'env = { '+', '.join(k+' = '+json.dumps(v) for k,v in env.items())+' }\n'
 (root/'config/codex-fragmento.toml').write_text('\n'.join(fragments),encoding='utf-8')
 print('Inicializado. Configure credenciais e confira baselines antes de congelar.')
def freeze(root):
 config=safe(root)
 verify()
 for f in FAMILIES.values():
  with zipfile.ZipFile(PACKAGE/'referencias'/f'{f}.zip') as z:
   expected={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
  actual={p.relative_to(root/'codigo'/f).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'codigo'/f).rglob('*') if p.is_file()}
  assert actual==expected,'Codigo nao e baseline original: '+f
 for p,f in FAMILIES.items():
  assert not (Path(config['fotografias'])/f'{f}_teste').exists(),'Referencias ja congeladas'
 for p,f in FAMILIES.items():
  run([cli(root,'mcp-sentry.exe'),'approve','--manifest',root/'config'/f'manifest-{f}.json','--store',root/'estado'/f])
  run([cli(root,'mcp-sentry.exe'),'doctor','--manifest',root/'config'/f'manifest-{f}.json','--store',root/'estado'/f])
  harness.snapshot(config,p)
 print('Referencias locais congeladas. Nunca aprove variantes.')
def prepare(root,index):
 config=safe(root);assert 1<=index<=48
 row=rows()[index-1];rec=harness.prepare(config,row['versao'],row['repeticao'])
 prompts=read(root/'operador/pedidos-fixos.json')
 label={'low':'Low','medium':'Médio','high':'High'}[config['ambiente']['esforco']]
 print(json.dumps({'titulo':f'Teste v1 Luna {label} {index}','modelo':'gpt-6-luna','esforco':config['ambiente']['esforco'],'caso':row,'preparo':rec,'mensagens':[prompts['tarefas'][row['versao'][0]],prompts['revisao'],prompts['registro']]},ensure_ascii=False,indent=2))
def check(root):
 # Only static git apply --check. No gateway/backend/Google calls or approval.
 safe(root)
 for p,f in FAMILIES.items():
  for n in range(1,9):run(['git','-c','core.autocrlf=false','-c','core.eol=lf','apply','--check','--whitespace=nowarn',PACKAGE/'operador/patches'/f'{p}{n}.patch'],cwd=root/'codigo'/f)
 print('24 patches aplicaveis aos 3 baselines. Nenhuma variante executada.')
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('acao',choices=['verificar','inicializar','congelar','preparar','coletar','restaurar','checar-patches']);a.add_argument('--raiz',type=Path);a.add_argument('--esforco',choices=['low','medium','high'],default='high');a.add_argument('--numero',type=int);a.add_argument('--id');a.add_argument('--sem-instalar',action='store_true');v=a.parse_args()
 if v.acao=='verificar':return verify()
 assert v.raiz,'Informe --raiz';root=v.raiz.resolve()
 if v.acao=='inicializar':return init(root,v.esforco,not v.sem_instalar)
 if v.acao=='congelar':return freeze(root)
 if v.acao=='checar-patches':return check(root)
 if v.acao=='preparar':assert v.numero;return prepare(root,v.numero)
 config=safe(root)
 if v.acao=='coletar':assert v.id;print(json.dumps(harness.collect(config,v.id),ensure_ascii=False))
 else:
  for p in FAMILIES:harness.restore(config,p)
if __name__=='__main__':main()
