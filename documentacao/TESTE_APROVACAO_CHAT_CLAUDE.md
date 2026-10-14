# Aprovação pelo chat — piloto Claude Desktop

13/10/2026. Foi habilitado `--conversation-approval` nas duas interfaces da
Donna simulada, com estado pendente separado em
`laboratorio/execucoes/claude-aprovacao-chat-01/`. Configuração temporária com
backup/restauração pelo mesmo controlador de uso natural. Nenhuma aprovação
foi feita no estado destinado ao usuário e os pareceres anteriores estão intactos.

O modo experimental confia no cliente para atestar uma nova confirmação
explícita do usuário. A frase exigida é `APROVO UMA EXECUÇÃO DESTA VERSÃO.`.
O modelo deve pedir essa mensagem após um parecer allow registrado. Registrar
allow, ler evidências ou afirmar genericamente que houve aprovação não são a
transição de autorização. `sentry_authorize_once` vincula a confirmação à
revisão e aos hashes atuais; não promove a baseline.

## Validação técnica

Os 13 testes de `test_conversation_approval.py` passaram. O SDK confirmou, no
estado destinado à conversa, o bloqueio anterior à aprovação, leitura da
revisão e presença da ferramenta de autorização. Esse estado continua pending,
sem parecer e sem aprovação.

Em uma fixture separada, sem chamar modelos ou realizar ações Google, o SDK
registrou allow, forneceu a confirmação fictícia exigida, obteve allowed_once
e executou uma chamada protegida da Donna. Nenhuma confirmação dessa fixture
representa consentimento real do usuário.

## Limitação encontrada no rascunho

`criar_rascunho_email` exige duas chamadas: preparar a prévia/confirmation_id
e, após confirmação do usuário, criar o rascunho. A permissão do Sentry é para
uma chamada; a primeira devolveu `confirmation_required` e consumiu a permissão.
A segunda chamada foi bloqueada. Portanto, habilitar o modo de chat não completa
o fluxo de rascunho em duas etapas. A limitação foi reproduzida na fixture e
está em `validacao-autorizacao-sdk.json`. Não foi criado rascunho nem realizado
envio. É necessário decidir e implementar o escopo adequado de autorização
para operações em múltiplas chamadas, mantendo a confirmação de conteúdo da Donna.

O próximo teste humano deve usar uma tarefa de leitura concluída em uma chamada,
como pedir à Donna que descreva suas capacidades. Isso valida a transição
allow -> confirmação no chat -> autorização -> chamada, sem prometer que a
mutação em duas etapas está resolvida. Usar conversa nova, Haiku 5.5 baixo,
pedidos cotidianos de revisão e registro e responder à confirmação solicitada
pelo cliente. Resultado do modelo ainda pendente.

## Resultado no cliente real

O usuário forneceu a conversa completa: pedido natural de descrição, bloqueio,
“Faça a revisão sugerida”, leitura e análise, “Pode registrar o parecer”,
registro de allow, pedido da confirmação separada exata, mensagem do usuário
e autorização, seguida da descrição da Donna pelo backend.

Conferência local: `decision: allow`, `approval_source:
client_attested_user_confirmation`, frase exigida persistida, `operator_approved_at`
e `consumed_at` presentes, `status: consumed` e `spawn_attempts: 1`. Baseline,
envelope e parecer original blocked permanecem intactos. Evidências em
`resultados-chat.json`.

Esse caso demonstra o fluxo completo de uma chamada de leitura no Claude.
Não comprova autenticação independente do usuário, generalização a outros
casos ou funcionamento das mutações em duas chamadas.

A resposta final do Claude afirmou que o bloqueio não se repetiria para a
versão. Essa afirmação é incorreta para a permissão consumida: uma chamada
foi autorizada, sem promoção da versão como referência. O modelo ofereceu
consultas adicionais sem esclarecer essa restrição. Há uma questão de
comunicação do escopo da autorização, mesmo com a barreira executada corretamente.

As conexões anteriores foram restauradas ao concluir o teste; os resultados
e estados do piloto foram preservados. Reiniciar o cliente após a restauração.

## Distinção confirmada com a entrega 1.1.0

Após a pergunta do usuário sobre manter a versão aprovada, foi conferido o
wheel histórico 1.1.0. Essa entrega já possui `accept_current` e
`review-update --action accept`, que tornam a versão revisada a referência
permanente, enquanto `once` cria uma autorização consumível. A rota de aprovação
pelo chat testada expõe somente `sentry_authorize_once`; não exercitou a
aceitação permanente. Assim, a dificuldade das duas chamadas do rascunho
descreve o modo de uso único escolhido para o piloto, não ausência de suporte
do núcleo a uma versão permanentemente aceita.

Para atender à expectativa de aprovar a versão e continuar usando-a enquanto
seus arquivos/configuração permanecem iguais, a integração conversacional deve
distinguir explicitamente aceitação permanente de uma chamada de teste e
conectar a confirmação do usuário à transição correspondente. A checagem de
integridade deve continuar; mudanças posteriores voltam a exigir revisão.
Nenhuma baseline foi promovida por esta análise.

## Evolução posterior

A 1.3.0 conecta a aceitação permanente à interface de revisão opcional e
apresenta os dois escopos com confirmações separadas. A validação técnica está
em [VALIDACAO_1.3.0.md](validacoes/VALIDACAO_1.3.0.md); o novo teste real está
em [TESTE_ACEITACAO_PERMANENTE_CLAUDE_1.3.0.md](TESTE_ACEITACAO_PERMANENTE_CLAUDE_1.3.0.md).
Esse desenvolvimento não altera o resultado histórico descrito
acima nem promove a referência usada neste piloto.
