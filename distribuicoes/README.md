# Pacotes para entregar ao usuário

O pacote atual é `mcp-sentry-1.3.0.zip`, com assistente para Codex e Claude
Desktop e aceitação permanente da versão pelo chat, mediante ativação opcional
e confirmação separada. A instalação e o transporte foram validados
tecnicamente; os testes reais deste novo fluxo no Claude continuam pendentes.
Os ZIPs 1.1.0 e 1.2.0 permanecem preservados.
Cada ZIP contém a pasta `instalar-mcp-sentry/`,
pronta para extrair e seguir seu README. O usuário dá dois cliques em
`INSTALAR.cmd`; instalações novas ficam em `%LOCALAPPDATA%\MCP-Sentry-Gateway`.
Os guias ficam em `ajuda/` e são copiados junto ao programa instalado.
As somas dos ZIPs estão em `SHA256SUMS.txt`; dentro de cada pacote há outra
lista de somas para os arquivos de instalação.

Os pacotes são preparados e validados por
[`preparar_distribuicao.py`](../desenvolvimento/distribuicao/README.md).
Python e o servidor MCP protegido continuam sendo pré-requisitos externos.
