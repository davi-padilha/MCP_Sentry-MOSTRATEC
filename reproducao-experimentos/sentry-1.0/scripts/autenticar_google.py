"""Login local explicito do operador; nao usado nas revisoes."""
import argparse,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,required=True);a=p.parse_args();r=a.raiz.resolve()
assert (r/'.bateria-sentry-portatil').is_file()
sys.dont_write_bytecode=True
sys.path.insert(0,str(r/'codigo/donna'))
from donna_mcp.providers.google import load_google_credentials
load_google_credentials(r/'credenciais/donna/credentials.json',r/'credenciais/donna/token.json',allow_interactive=True)
print('Token local pronto; nao copie credenciais para o repo.')
