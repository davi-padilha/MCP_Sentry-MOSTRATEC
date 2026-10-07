# Validação técnica da candidata 0.9.0

06/10/2026. Evolução solicitada após a auditoria da bateria da 0.8.1: corrigir
a apresentação do código e acrescentar políticas explícitas de privacidade.
Código e documentação preparados com assistência do Codex. Não houve commit
ou push, instalação sobre a série antiga ou novas revisões com IA.

## Implementação

- O reconhecedor de segredos exige fechamento de chaves entre aspas antes de
  uma atribuição. Literais como `"password="` e `"token="` não são interpretados
  como chaves. Strings comuns não atravessam quebras físicas de linha; valores
  entre aspas triplas e blocos PEM conservam suas quebras de linha ao mascarar.
- `privacy_policy` é uma declaração opcional do operador com regras por
  ferramenta, requisitos e listas de campos. O esquema rejeita ferramentas
  inexistentes, regras duplicadas e listas contraditórias.
- A política aprovada fica vinculada ao envelope confiado, fora do código do
  servidor. O dossiê apresenta a política aprovada, seu hash e qualquer
  proposta diferente. Pareceres e aceitação de código não promovem regras.
- Alterar regras requer promoção separada pelo operador e nova revisão do
  dossiê. A interface MCP não promove a política. O protocolo de pareceres
  passou a `mcp-sentry-review-v2`.

As políticas são contexto para revisão semântica, **não filtros de respostas
durante a execução nem certificação de conformidade**. O mascaramento continua
sendo reconhecimento textual dos formatos cobertos; não é um sistema geral
de prevenção de vazamento. Hashes de integridade continuam calculados sobre
os bytes originais, sem executar os arquivos para analisá-los.

## Verificações

O comando `python -B -m unittest discover -s desenvolvimento/gateway/testes -q`
passou na rodada final: **90 testes, um ignorado por indisponibilidade de
symlink na plataforma**. Os 14 testes novos cobrem o defeito dos literais,
segredos em JSON, aspas escapadas, valores multilinha, PEM e conservação de
linhas/definições; também cobrem exposição da política pelas duas rotas MCP,
validação, enfraquecimento/remoção/adição de regras, bloqueio de execução,
promoção separada e invalidação de evidência antiga. Avisos preexistentes de
localização Python no sandbox e de `maxsplit` posicional não impediram os testes.

O wheel foi instalado em um ambiente descartável separado. Todos os seus
14 módulos Python coincidiram byte a byte com a fonte validada. Um replay
técnico dos 24 patches congelados confirmou sintaxe, linhas físicas e
definições preservadas nos arquivos apresentados e entrega das regras pela
interface de revisão. Python foi conferido por AST e JavaScript por
`node --check`. Esses snapshots são mínimos para verificar a representação;
não constituem instalações completas dos servidores nem novas revisões da
bateria. Nenhum backend protegido ou recurso Google foi executado no replay.

## Distribuição

Wheel: `pacote-usuario/mcp_sentry_gateway-0.9.0-py3-none-any.whl`.

SHA256: `329f806338e33cc211326fe77b3e75df559beb2060ccc15c18d8d3321899f7c8`.

O build usou dependências de empacotamento isoladas, sem instalar a candidata
no ambiente da 0.8.1. Os wheels 0.8.0/0.8.1 e os resultados anteriores foram
preservados. [Manual de privacidade](../desenvolvimento/gateway/PRIVACIDADE.md)
e cópia para o usuário em `pacote-usuario/PRIVACIDADE.md`.

## Antes da nova série

Definir e revisar a política efetiva, conferir compatibilidade com a
referência e as classes esperadas, fixar versão/hashes e preparar estados e
registros separados. Uma regra nova pode contradizer dados já retornados pela
referência e alterar a interpretação do gabarito; esse conflito precisa ser
resolvido no protocolo antes da coleta. Nenhuma política de exemplo foi
aplicada automaticamente aos servidores reais.

GPT-6 Luna/Médio foi solicitado e aparece como `gpt-6-luna`/`medium` no catálogo
local do Codex. Sua escolha deve ser confirmada em cada rollout da nova série;
o catálogo não substitui a verificação da execução efetiva. A definição de
quais séries comparar e o tratamento das incompatibilidades ainda acompanham
a preparação. Trocar gateway, regras e modelo juntos mede essa combinação;
não isola o efeito individual de cada mudança.

Evidências específicas e propostas de política ficam na área privada do
operador, separadas do repositório e dos workspaces de revisão. O caderno de
campo deve registrar implementação, conferências e decisões posteriores.

## Adendo: compatibilidade com as ferramentas nativas

Em conferência posterior ao replay, foram usadas cópias integrais das
referências nativas de Filesystem, Git e Donna e o wheel instalado da
candidata, com estados descartáveis. Os catálogos completos mantiveram
**39 ferramentas**: 14 Filesystem, 12 Git e 13 Donna. O gateway verificou o
catálogo exato do backend antes de encaminhar as chamadas.

**36 chamadas de leitura** foram comparadas com a rota direta, em cenários
sem política e com política compatível confiada no laboratório. Incluíram
arquivos vazios e múltiplos arquivos, busca e listagem, status/histórico/diffs
Git, agenda/horários livres, busca/leitura de e-mails e anexo fictício.
As respostas foram equivalentes. Foram normalizados somente defaults
opcionais de representação do SDK MCP e o endereço de memória variável do
objeto de fuso horário que o próprio `git_show` imprime; a equivalência foi
confirmada também repetindo essa chamada diretamente.

Não houve erros das ferramentas nessas chamadas, envios ou mutações Google,
aprovações do ambiente ativo, revisões com IA, alteração dos casos ou
commit/push. A proteção das fontes, configurações, aprovações e patches
monitorados foi conferida durante a continuação dos controles. O registro
privado documenta a preparação interrompida e o diagnóstico da representação
variável, sem tratá-los como resultados da bateria.

Essa cobertura confirma os catálogos e as leituras exercitadas; não garante
todos os fluxos de escrita, todas as entradas ou o cliente desktop. As regras
devem preservar o contrato funcional e as autorizações legítimas. Elas
orientam a revisão, sem eliminar campos da resposta nativa. Uma mudança de
política ainda exige promoção separada do envelope confiado; uma política
já confiada e inalterada não exige promoção a cada chamada.
