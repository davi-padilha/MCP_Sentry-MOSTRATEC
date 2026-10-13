# MCP Sentry 1.3.0 — comece aqui

O Sentry protege um servidor MCP local: se a implementação mudar, ele
interrompe seu uso e oferece evidências para revisão antes de uma autorização.

## Instalar em três passos

1. **Prepare os requisitos:** Windows, Python 3.11+ com pip/venv,
   seu cliente de IA e o servidor MCP já funcionando. Se precisar de Python,
   use o [download oficial para Windows](https://www.python.org/downloads/windows/).
2. **Extraia o ZIP inteiro.** Abra a pasta `instalar-mcp-sentry` extraída;
   mantenha seus arquivos e subpastas juntos durante a instalação.
3. **Dê dois cliques em `INSTALAR.cmd`.** O instalador confere os arquivos,
   encontra Python e instala o programa. Ao terminar uma instalação nova,
   oferece abrir o assistente. Escolha `s` e selecione Codex ou Claude Desktop.

O assistente mostra o MCP escolhido e pede confirmações separadas para
descobrir ferramentas, aprovar a referência e substituir a conexão direta.
Depois de conectar, reinicie as conexões do cliente e confira o uso pelo Sentry.

**O programa usa uma pasta fixa:** `%LOCALAPPDATA%\MCP-Sentry-Gateway\`.
É uma pasta do seu perfil Windows. Após instalar, pode remover o ZIP e a
pasta extraída. O resumo mostra onde o programa e sua ajuda foram instalados.
Instalações antigas mantêm seus caminhos; veja o guia de atualização abaixo.

**Confirmação pelo chat é opcional:** o guia de uso explica como ativá-la e
escolher entre aceitar uma versão permanentemente e autorizar uma chamada.
Um parecer favorável da IA, sozinho, não libera o servidor.

## Onde encontrar ajuda

- [Uso, atualização e restauração](ajuda/USO-E-ATUALIZACAO.md).
- [Problemas de instalação ou configuração](ajuda/SOLUCAO-DE-PROBLEMAS.md).
- [Configuração manual e outros clientes](ajuda/CONFIGURACAO.md).
- [Privacidade e limites da revisão](ajuda/PRIVACIDADE.md).

`arquivos-instalacao` contém os componentes usados pelo instalador. Não é
necessário abrir ou editar esses arquivos para a instalação normal.

O assistente atende Codex e Claude Desktop. Outros clientes exigem configuração manual e
suporte a MCP local por `stdio`. O pacote não inclui Python, o servidor MCP
protegido nem suas credenciais. Não requer o restante do repositório.

Uma recomendação da IA não autoriza execução: a decisão permanece com o
operador. A proteção cobre a rota e os arquivos configurados; não é sandbox.
