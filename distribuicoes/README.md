# Pacotes para entregar ao usuário

O pacote atual é `mcp-sentry-1.3.1.zip`, com assistente para Codex e Claude
Desktop e aceitação permanente da versão pelo chat, mediante ativação opcional
e confirmação separada. A instalação e o transporte foram validados
tecnicamente. O teste real do fluxo natural no Claude passou nos controles de
execução e persistência, com falhas de comunicação descritas em
[TESTE_ACEITACAO_PERMANENTE_CLAUDE_1.3.0.md](../documentacao/TESTE_ACEITACAO_PERMANENTE_CLAUDE_1.3.0.md).
Na 1.3.1, o bloqueio e as instruções oferecem explicitamente uma revisão
somente leitura pelo cliente, a pedido do usuário. Essa oferta foi observada
na rodada real registrada em
[TESTE_OFERTA_REVISAO_CLAUDE_1.3.1.md](../documentacao/TESTE_OFERTA_REVISAO_CLAUDE_1.3.1.md),
com limitações nas etapas posteriores e sem garantia de consistência geral.
Os ZIPs 1.1.0, 1.2.0 e 1.3.0 permanecem preservados.
Cada ZIP contém a pasta `instalar-mcp-sentry/`,
pronta para extrair e seguir seu README. O usuário dá dois cliques em
`INSTALAR.cmd`; instalações novas ficam em `%LOCALAPPDATA%\MCP-Sentry-Gateway`.
Os guias ficam em `ajuda/` e são copiados junto ao programa instalado.
As somas dos ZIPs estão em `SHA256SUMS.txt`; dentro de cada pacote há outra
lista de somas para os arquivos de instalação.

Os pacotes são preparados e validados por
[`preparar_distribuicao.py`](../desenvolvimento/distribuicao/README.md).
Python e o servidor MCP protegido continuam sendo pré-requisitos externos.
