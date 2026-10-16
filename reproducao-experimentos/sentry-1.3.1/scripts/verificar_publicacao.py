"""Reconcilia somente os campos publicos das quatro campanhas historicas 1.3.1."""
import csv,hashlib,json,math
from pathlib import Path
from exportar_resultados import SERIES,TOKEN_FIELDS
REPO=Path(__file__).resolve().parents[3]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
 totals={'principal':0,'diagnostico':0,'tecnica_excluida':0,'turnos':0}
 for _,name,_ in SERIES:
  root=REPO/'pesquisa/02_resultados'/name;summary=read(root/'resumo.json');provenance=read(root/'proveniencia.json')
  for n,digest in provenance['arquivos_publicos_sha256'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==digest,n
  units=rows(root/'execucoes_publicas.csv');turns=rows(root/'turnos_publicos.csv');ids={r['tentativa_anonima'] for r in units}
  assert len(ids)==len(units) and all(r['tentativa_anonima'] in ids for r in turns)
  for unit in units:
   ts=[t for t in turns if t['tentativa_anonima']==unit['tentativa_anonima']]
   assert len(ts)==int(unit['turnos'])
   assert all(t['uso']==unit['uso'] for t in ts)
   assert unit['tokens_observaveis']=='True'
   for k in TOKEN_FIELDS:assert int(unit[k])==sum(int(t[k]) for t in ts)
   assert math.isclose(float(unit['duracao_turnos_segundos']),sum(float(t['duracao_segundos']) for t in ts),abs_tol=.002)
   assert unit['backend_iniciado']=='False'
  for use,key in [('principal','principal'),('diagnostico','R3'),('tecnica_excluida','tecnica_excluida')]:
   rs=[r for r in units if r['uso']==use];expected=summary['consumo'][key]
   assert len(rs)==expected['revisoes']
   for k in TOKEN_FIELDS:assert sum(int(r[k]) for r in rs)==expected['tokens'][k]
   assert math.isclose(sum(float(r['duracao_turnos_segundos']) for r in rs),expected['duracao_turnos_segundos'],abs_tol=.002)
   totals[use]+=len(rs)
  primary=[r for r in units if r['uso']=='principal']
  assert len(primary)==48 and len({(r['caso_anonimo'],r['repeticao']) for r in primary})==48
  assert sum(r['inconclusivo']=='True' for r in primary)==summary['principais']['inconclusivas']
  totals['turnos']+=len(turns)
 assert totals=={'principal':192,'diagnostico':8,'tecnica_excluida':2,'turnos':602},totals
 print(json.dumps(totals));print('Hashes, selecao, duracoes e tokens publicos reconciliados.')
if __name__=='__main__':main()
