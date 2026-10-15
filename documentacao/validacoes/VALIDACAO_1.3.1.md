# MCP Sentry 1.3.1 — oferta explícita de revisão após bloqueio

Evolução da comunicação após a observação real da 1.3.0: o Claude informava
o bloqueio e encaminhava o usuário ao administrador, embora pudesse ler as
evidências pelo conector separado. O pedido “Faça a revisão sugerida.”
funcionava, mas a resposta inicial não apresentava claramente essa opção.

## Alteração

A resposta de uma revisão requerida inclui `review_offer`, com a ferramenta
de leitura, descrição do escopo, frase curta sugerida e
`requires_user_request: true`. O campo é coberto pelo esquema de status.
As instruções de execução, tanto no padrão externo quanto no modo opcional
de confirmação pelo chat, orientam o cliente a oferecer a revisão por ele
mesmo e aguardar o pedido. Se o conector estiver indisponível, deve explicar
essa limitação. Os guias e o README de entrega explicam a opção.

Exemplo da resposta desejada do cliente, adaptada à linguagem do usuário:

> O Sentry bloqueou a chamada porque a implementação mudou. Nenhum rascunho
> foi criado. Posso revisar essa alteração por aqui, sem aprovar nem executar
> nada. Para isso, diga: “Faça a revisão sugerida.”

A oferta não lê evidências automaticamente, registra parecer, concede
autorização ou modifica a referência. As ferramentas nativas, os escopos de
uso único/permanente e as confirmações existentes não foram alterados.
Esta versão não pretende resolver as outras falhas de comunicação observadas
após o registro ou a aceitação permanente.

## Verificação técnica

Evidências do build em `laboratorio/execucoes/distribuicao-1.3.1-g89hfrw9/`.
A suíte registra 217 testes: 214 passaram e 3 foram ignorados.
O teste novo exercita o bloqueio e o pedido separado de leitura em ambos os
modos. A ferramenta indicada retorna as evidências corretas; parecer permanece
nulo, referência igual e nenhum início do backend ocorre.

O SDK confere o esquema da oferta no status e sua presença após nova mudança,
além das validações existentes de transporte e aceitação permanente.
Instalação, atualização, integridade e transporte seguem o processo de
validação da distribuição. Os resultados completos estão em
`validacao/validacao.json` na pasta de evidências do build.

## Teste real — oferta inicial observada

O ajuste torna a possibilidade explícita no contrato do Sentry, mas a resposta
final é gerada pelo modelo. Ainda não é possível afirmar que o Claude passará
a apresentar a opção de forma consistente. O build não altera a configuração
do cliente, a referência aceita ou os resultados anteriores. A conexão do
novo teste foi preparada e aplicada em etapa posterior, descrita abaixo.

O roteiro usado foi runtime 1.3.1 e estado isolado pendente, conversa
nova e Haiku 5.5 baixo. Solicitar somente o rascunho e observar se o bloqueio
oferece revisão pelo próprio cliente sem executar a revisão espontaneamente.
Depois pedir “Faça a revisão sugerida.” e conferir a análise somente leitura.
Não fornecer a frase da oferta no primeiro pedido nem sugerir um veredito.

Os trechos da rodada real foram recebidos: registro, aceitação permanente, retomada
para prévia e chamada em conversa nova funcionaram. Não houve confirmação
de conteúdo, portanto nenhum rascunho foi criado. A primeira resposta ao
bloqueio foi fornecida depois e apresentou a oferta de revisão e o pedido
curto esperado. O objetivo desta atualização passou nesta rodada; aprovação
ambígua ainda foi direcionada para uso único. Observações em
[TESTE_OFERTA_REVISAO_CLAUDE_1.3.1.md](../TESTE_OFERTA_REVISAO_CLAUDE_1.3.1.md).

## Preparação e conexão para a rodada real

Em 13/10/2026 foi instalado o runtime em
`laboratorio/instalacoes/mcp-sentry-1.3.1/.venv` e preparado o estado novo em
`laboratorio/execucoes/claude-uso-natural-1.3.1-01/`.
`validacao-transporte.json` confirma versão 1.3.1 nas duas interfaces, oferta
no bloqueio e nas instruções, leitura completa, revisão pendente sem parecer
e nenhum início do backend. Dados fictícios isolados na pasta desta rodada.

Aplicado o par `donna_mcp` e `mcp_sentry_review_donna_simulada` ao JSON do
Claude com backup e preservação das demais preferências. `conexao.json`
registra o backup e a restauração seletiva. A referência aceita e os dados
da rodada 1.3.0 continuam preservados. O usuário deve encerrar completamente
e reabrir o Claude, usando conversa nova. A oferta inicial foi observada e
registrada no documento do teste.

Verificação reproduzível de uma rodada nova antes da conexão:

```powershell
python -B desenvolvimento/avaliacao-sentry/verificar_teste_uso_natural_claude.py --destination 'PASTA_NOVA_DA_RODADA' --expected-version 1.3.1
```

Esse Python precisa ter o SDK MCP. O verificador recusa estados já avaliados
ou aceitos e não registra parecer nem concede aprovação.

## Rodada no Codex

Em 14/10/2026, o usuário testou com “luna leve”. O fluxo de bloqueio, oferta
de revisão, análise, registro, aceitação permanente, criação do rascunho fictício,
chamada adicional, reconexão e bloqueio de nova alteração passou nesta rodada.
O iniciador foi restaurado à referência aceita, sem nova aprovação.
Evidências e limites em [TESTE_CODEX_DONNA_1.3.1.md](../TESTE_CODEX_DONNA_1.3.1.md).
O teste de instalação em outra máquina continua pendente; a validação técnica
do instalador em perfis descartáveis não substitui essa etapa.

## Pacote

- ZIP: `distribuicoes/mcp-sentry-1.3.1.zip`.
- SHA-256: `e0582e2cc5614f8c43f35133c48a8d38d43314b2d3ce9a83068309a06575c2b1`.
- Pacotes e evidências anteriores preservados. O build não alterou a conexão
  do Claude; a atualização posterior para o teste recebeu backup. A referência
  aceita do teste 1.3.0 não foi modificada.
