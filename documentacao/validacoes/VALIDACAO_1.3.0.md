# MCP Sentry 1.3.0 — aceitação permanente pelo chat

Correção concluída e validada tecnicamente em 13/10/2026. O teste do novo fluxo
com um modelo no Claude Desktop permanece pendente. Nenhuma configuração ativa
do Claude foi alterada por esta validação. Claude Code permanece como etapa posterior.

## Comportamento

No modo opcional `--conversation-approval`, a interface separada de revisão
oferece duas decisões após um parecer `allow` registrado:

- `sentry_accept_version`: aceita exatamente a versão revisada como referência
  permanente após nova confirmação `ACEITO ESTA VERSÃO COMO REFERÊNCIA PERMANENTE.`.
  Chamadas repetidas e reconexões continuam permitidas enquanto o escopo
  inspecionado coincidir com essa referência. Nova alteração volta a bloquear.
- `sentry_authorize_once`: autoriza uma chamada após nova confirmação
  `APROVO UMA EXECUÇÃO DESTA VERSÃO.`. Uma prévia também consome a permissão;
  ela não aceita a versão permanentemente.

As descrições, instruções de inicialização e recibo do parecer apresentam os
dois escopos. Aprovação ambígua deve provocar esclarecimento, sem escolha
silenciosa. A ferramenta de aceitação exige o parecer vigente registrado pelo
cliente, a frase correspondente e os hashes da revisão. Revisar ou registrar
parecer não aceita uma versão. O modo padrão de aprovação externa permanece.

A referência só é substituída após persistir evidências obrigatórias e
reconferir código, referência e envelope de execução. Falhas de gravação ou
divergências preservam o bloqueio. Evidências ausentes ou alteradas após a
aceitação também bloqueiam. Configuração, cobertura, política de privacidade
e catálogo declarado não são promovidos por essa ferramenta. Se houver uma
cópia antiga em execução, ela é encerrada antes de iniciar a versão aceita.

Status distingue parecer registrado, autorização de uma chamada consumida e
versão aceita. O campo antigo `semantic_review_status` foi mantido por
compatibilidade, com `assessment_recording_status` para tornar explícito que
ele registra a presença de um parecer. Um hash aprovado não certifica
segurança, privacidade ou comportamento de dependências externas.

O assistente e os preparadores aceitam `--conversation-approval`; o instalador
aceita `-Configurar -AprovarNoChat`. O diagnóstico confere a opção nas duas
interfaces. As confirmações pelo chat são atestadas pelo cliente, sem
autenticação independente da mensagem humana. O estado deve ser protegido
contra escrita pelo agente; o laboratório não comprova esse isolamento.

## Evidências técnicas

- Build e instalação: `laboratorio/execucoes/distribuicao-1.3.0-wekthnxw/`.
  `validacao/validacao.json` registra **216 testes: 213 passaram, 3 ignorados**,
  19 módulos idênticos entre fonte, wheel e instalação, instalação limpa,
  atualização da 1.0.0 para 1.3.0 com estado preservado, integridade do pacote,
  lançador CMD, setup, diagnóstico e restauração em configurações fictícias.
- Os 21 testes específicos de aceitação incluem vínculos inválidos, revisão
  expirada, ausência de parecer favorável, configurações não promovíveis,
  falhas de gravação, mudanças durante a aceitação, concorrência entre escopos,
  auditoria ausente/divergente, reconexão e substituição do backend antigo.
- O SDK oficial MCP conferiu esquemas e chamadas por `stdio`: quatro ferramentas
  de revisão no padrão, seis com ativação opcional, aceitação, chamadas repetidas,
  reconexão e nova alteração bloqueada com `spawn_attempts: 0`.
- Donna: `laboratorio/execucoes/validacao-donna-permanente-1.3.0/`.
  A fixture ficou bloqueada antes do início; registrar `allow` manteve a
  referência; aceitar não iniciou o servidor. A prévia e a confirmação criaram
  um rascunho fictício. Outra chamada funcionou e, após reconectar, repetir a
  confirmação retornou o mesmo rascunho sem duplicá-lo. Fonte e evidências
  originais foram preservadas. Nenhuma ação Google realizada.

Reprodução da validação Donna com um Python que tenha o SDK MCP:

```powershell
python -B desenvolvimento/avaliacao-sentry/verificar_aceitacao_permanente_donna.py --demo 'PASTA_DA_DEMO_SIMULADA' --destination 'PASTA_NOVA_DE_EVIDENCIAS' --gateway-python 'PYTHON_DO_GATEWAY_INSTALADO'
```

Esses pareceres e confirmações são entradas de teste; não representam decisão
de um modelo nem aprovação do usuário sobre a demonstração ativa.

## Próximo teste no Claude Desktop

Preparar uma revisão nova em estado isolado e conectar somente o par simulado,
com backup. Usar os pedidos naturais de rascunho, revisão e registro. Depois
testar uma aprovação ambígua: o Claude deve esclarecer o escopo. Escolher
aceitação permanente, confirmar como solicitado e concluir a confirmação de
conteúdo da Donna. Conferir outra chamada e reinício do Claude sem nova
aprovação. Em estados separados, conferir consumo de uma chamada e alteração
posterior bloqueada. Registrar as respostas e confrontá-las com o estado local.

Não fornecer um veredito ao modelo nem afirmar que o comportamento do cliente
está corrigido antes dessa observação. Os testes anteriores não estabelecem
causalmente se a decisão inicial decorreu do modelo ou da apresentação do Sentry.

## Pacotes

- ZIP: `distribuicoes/mcp-sentry-1.3.0.zip`.
- SHA-256: `c438d5dca9fa3003bc8c6f63c732448a508ba8bb0c1ff124f87765e9902c81a9`.
- ZIPs 1.1.0 e 1.2.0 preservados com hashes inalterados; wheels anteriores
  arquivados em `distribuicoes-historicas/`.
