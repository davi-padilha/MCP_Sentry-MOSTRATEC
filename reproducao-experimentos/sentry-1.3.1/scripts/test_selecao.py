"""Regressoes do seletor; sem modelos, gateway, Google ou dados reais."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
import selecionar as s
class SelectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();p=self.root/'evidencia.txt';p.write_bytes(b'fixture privada ficticia')
  self.registry=[];self.items=[]
  for i,pos in enumerate(s.bateria.rows()):
   r={'id':str(i),'versao':pos['versao'],'repeticao':pos['repeticao'],'parecer_ia':'liberar','inconclusivo':'','servidor_iniciado':'nao'};self.registry.append(r)
   self.items.append({'id':str(i),'uso':'principal','evidencias_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()},'motivo_tecnico':'','autorizacao_reposicao':'','auditoria_manual':{'modelo':'gpt-6.1-sol','esforco':'low','turnos_concluidos':['a','b','c'],**{k:True for k in s.CHECKS},'recibo_confere_persistencia':True}})
 def check(self):return s.validate(self.registry,{'tentativas':self.items},'gpt-6.1-sol','low',self.root)
 def add_r3(self,version):
  r=copy.deepcopy(next(r for r in self.registry if r['versao']==version));r.update(id='r3',repeticao='R3');self.registry.append(r)
  item=copy.deepcopy(self.items[0]);item.update(id='r3',uso='R3');self.items.append(item)
 def test_valid_complete(self):self.assertEqual(len(self.check()[0]),48)
 def test_duplicate_cannot_replace_other_position(self):
  self.registry[0]['versao']=self.registry[1]['versao'];self.registry[0]['repeticao']=self.registry[1]['repeticao']
  with self.assertRaises(AssertionError):self.check()
 def test_wrong_effective_model(self):
  self.items[0]['auditoria_manual']['modelo']='gpt-6-luna'
  with self.assertRaises(AssertionError):self.check()
 def test_distinct_completed_turns(self):
  self.items[0]['auditoria_manual']['turnos_concluidos']=['a','a','b']
  with self.assertRaises(AssertionError):self.check()
 def test_missing_receipt_is_inconclusive_not_exclusion(self):
  self.registry[0]['inconclusivo']='sem recibo';self.registry[0]['parecer_ia']='inconclusivo';self.items[0]['auditoria_manual']['recibo_confere_persistencia']=False
  self.add_r3(self.registry[0]['versao']);self.assertEqual(len(self.check()[0]),49)
 def test_conclusive_requires_receipt(self):
  self.items[0]['auditoria_manual']['recibo_confere_persistencia']=False
  with self.assertRaises(AssertionError):self.check()
 def test_r3_only_disagreement(self):
  self.add_r3(self.registry[0]['versao'])
  with self.assertRaises(AssertionError):self.check()
 def test_technical_requires_authorization_and_preservation(self):
  r=copy.deepcopy(self.registry[0]);r['id']='tech';self.registry.append(r)
  item=copy.deepcopy(self.items[0]);item.update(id='tech',uso='tecnica_excluida',motivo_tecnico='fixture shell');self.items.append(item)
  with self.assertRaises(AssertionError):self.check()
  item['autorizacao_reposicao']='autorizacao ficticia de teste';self.assertEqual(len(self.check()[1]),1)
 def test_changed_evidence_rejected(self):
  (self.root/'evidencia.txt').write_bytes(b'mudou')
  with self.assertRaises(AssertionError):self.check()
if __name__=='__main__':unittest.main()
