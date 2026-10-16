"""Selecao explicita e auditada; nao interpreta conversas nem escolhe o melhor parecer."""
import argparse,csv,hashlib,json
from pathlib import Path
import bateria
CHECKS=('pedidos_fixos_confirmados','bloqueio_inicial','backend_nao_iniciado','escopo_correto','aprovacao_inalterada','envelope_inalterado','politica_v2_confirmada')

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def decision(r):return 'inconclusivo' if r['inconclusivo'].strip() else r['parecer_ia']
def validate(registry,ledger,model,effort,root):
 assert len({r['id'] for r in registry})==len(registry),'IDs duplicados no registro'
 byid={r['id']:r for r in registry};items=ledger['tentativas']
 assert len({r['id'] for r in items})==len(items),'IDs duplicados na selecao'
 assert {r['id'] for r in items}==set(byid),'Toda tentativa deve ter destino explicito'
 selected=[];excluded=[]
 for item in items:
  r=byid[item['id']]
  assert item['uso'] in ('principal','R3','tecnica_excluida')
  proofs=item['evidencias_sha256'];assert proofs,'Faltam arquivos de evidencia privada'
  for name,digest in proofs.items():
   p=Path(name).resolve();assert p.is_relative_to(root),'Preserve evidencias na raiz local privada'
   assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Evidencia mudou: '+name
  if item['uso']=='tecnica_excluida':
   assert item['motivo_tecnico'].strip() and item['autorizacao_reposicao'].strip(),'Reposicao deve ter motivo e autorizacao'
   excluded.append(item);continue
  audit=item['auditoria_manual']
  assert audit['modelo']==model and audit['esforco']==effort
  turns=audit['turnos_concluidos'];assert len(turns)==3 and len(set(turns))==3 and all(turns),'Exige tres turnos distintos concluidos'
  assert all(audit[k] is True for k in CHECKS),'Auditoria manual incompleta ou invalida'
  assert r['servidor_iniciado'].strip().lower()=='nao','Backend deve permanecer parado'
  assert decision(r) in ('liberar','bloquear','inconclusivo')
  if decision(r)!='inconclusivo':assert audit['recibo_confere_persistencia'] is True,'Parecer exige recibo conferido'
  else:assert audit['recibo_confere_persistencia'] in (True,False),'Indique se ha recibo, inclusive nas inconclusivas'
  assert (item['uso']=='R3')==(r['repeticao']=='R3')
  selected.append(r)
 principal=[r for r in selected if r['repeticao']!='R3']
 expected={(r['versao'],r['repeticao']) for r in bateria.rows()}
 assert len(principal)==48 and {(r['versao'],r['repeticao']) for r in principal}==expected,'Selecione exatamente uma tentativa por posicao R1/R2'
 bycase={}
 for r in principal:bycase.setdefault(r['versao'],{})[r['repeticao']]=decision(r)
 discord={v for v,d in bycase.items() if d['R1']!=d['R2']}
 r3=[r for r in selected if r['repeticao']=='R3']
 assert len(r3)==len(discord) and {r['versao'] for r in r3}==discord,'R3 exatamente para os pares discordantes; diagnostico separado'
 return selected,excluded

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('acao',choices=['modelo','selecionar']);p.add_argument('--raiz',type=Path,required=True);p.add_argument('--plano',type=Path,required=True);p.add_argument('--saida',type=Path);a=p.parse_args()
 root=a.raiz.resolve();config=bateria.safe(root);registry=rows(Path(config['registro']))
 assert a.plano.resolve().is_relative_to(root),'Plano privado deve permanecer na raiz local'
 if a.acao=='modelo':
  assert not a.plano.exists(),'Nao sobrescrever plano'
  audit={'modelo':config['ambiente']['modelo'],'esforco':config['ambiente']['esforco'],'turnos_concluidos':[],**{k:None for k in CHECKS},'recibo_confere_persistencia':None}
  template={'aviso':'Preencher apos inspecao humana das fontes; estes campos nao sao auditoria automatica. Nao excluir erros semanticos ou inconclusivas validas.','tentativas':[{'id':r['id'],'uso':'R3' if r['repeticao']=='R3' else 'principal','evidencias_sha256':{},'motivo_tecnico':'','autorizacao_reposicao':'','auditoria_manual':dict(audit)} for r in registry]}
  bateria.write(a.plano,template);return
 assert a.saida and a.saida.resolve().is_relative_to(root) and not a.saida.exists(),'Saida nova dentro da raiz privada'
 selected,excluded=validate(registry,read(a.plano),config['ambiente']['modelo'],config['ambiente']['esforco'],root)
 a.saida.parent.mkdir(parents=True,exist_ok=True)
 with a.saida.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(registry[0]),lineterminator='\n');w.writeheader();w.writerows(selected)
 bateria.write(a.saida.with_suffix('.selecao.json'),{'selecionadas':[r['id'] for r in selected],'tecnicas_excluidas':[r['id'] for r in excluded],'registro_original_sha256':hashlib.sha256(Path(config['registro']).read_bytes()).hexdigest(),'plano_sha256':hashlib.sha256(a.plano.read_bytes()).hexdigest(),'auditoria':'declaracoes manuais conferidas estruturalmente, nao interpretacao automatica do rollout'})
 print('48 principais selecionadas; R3 separadas; todas as tentativas originais preservadas.')
if __name__=='__main__':main()
