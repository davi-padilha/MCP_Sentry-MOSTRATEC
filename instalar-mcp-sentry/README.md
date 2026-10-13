# Instalar o MCP Sentry 1.1.0

Esta pasta contém tudo que precisa receber para instalar o gateway. O Sentry
confere código e configuração de um servidor MCP local contra uma referência
aprovada; alterações permanecem bloqueadas até revisão e decisão do operador.

## Antes de começar

- Windows com Python 3.11 ou posterior, incluindo `venv` e `pip`.
  As versões efetivamente testadas estão em `VERSAO.json`.
- Seu servidor MCP e seu runtime (Python ou Node), funcionando separadamente.
- Um cliente que aceite MCP local via `stdio`. O assistente configura Codex;
  outros clientes exigem a preparação manual de `CONFIGURACAO.md`.
- Suas próprias credenciais e dados, se exigidos pelo MCP.

O pacote não inclui Python, seu servidor MCP nem credenciais. Não precisa
baixar o restante do repositório. Extraia o ZIP antes de instalar e mantenha
a pasta em um caminho estável, fora do código protegido e das pastas que o
agente pode editar. Não mova a pasta depois de conectar os MCPs.

## 1. Instalar

Abra PowerShell nesta pasta:

```powershell
.\instalar.ps1
```

O instalador confere as somas dos arquivos, procura um Python compatível,
cria `.venv` e instala o wheel local, sem download de dependências do gateway.
Mostra a versão e os caminhos instalados. Em uma instalação nova, pergunta
se deseja abrir o assistente de configuração; Enter significa não.

Para apenas instalar, sem perguntas de configuração:

```powershell
.\instalar.ps1 -SemConfigurar
```

Se o Python não for encontrado ou um atalho do Windows não funcionar:

```powershell
.\instalar.ps1 -PythonExe 'C:\CAMINHO\python.exe'
```

Para solicitar o assistente ao terminar a instalação:

```powershell
.\instalar.ps1 -Configurar
```

O assistente mantém as confirmações para descobrir ferramentas, aprovar a
referência inicial e alterar a configuração. `-Configurar` não aprova nada.

Se a política do Windows impedir o script, use a instalação manual abaixo.
Troque `py -3` pelo caminho do Python se o launcher não estiver disponível:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --no-deps .\mcp_sentry_gateway-1.1.0-py3-none-any.whl
```

Confira as somas antes da instalação manual. Os hashes detectam diferença
em relação à lista recebida; não autenticam o remetente.

## 2. Conectar seu MCP no Codex

Se não abriu o assistente ao instalar, com o MCP já configurado no Codex:

```powershell
.\.venv\Scripts\mcp-sentry.exe setup
```

O assistente mostra os servidores suportados, os arquivos e o catálogo.
A descoberta inicia o MCP uma vez; use somente código que autorizou executar.
Há confirmações distintas para descoberta, aprovação inicial e substituição
da conexão direta. A configuração recebe backup. Anote os caminhos do
manifesto, estado e `codex-installation.json` apresentados ao concluir.

O assistente aceita entradas Python/Node locais e formatos suportados de
`npx`/`uvx`. A preparação desses servidores pode exigir internet. Entradas
incompatíveis são recusadas. Consulte `CONFIGURACAO.md` para outros formatos.

Reinicie as conexões do Codex. Confira a execução via Sentry e a revisão
separada. Desative conexões diretas paralelas do mesmo MCP; elas não recebem
a proteção. "Programa instalado" não significa "MCP conectado".

## 3. Usar e conferir

Use as ferramentas normalmente. Com a referência inalterada, argumentos e
respostas nativas são preservados. Uma alteração provoca bloqueio antes do
início da nova implementação.

```powershell
.\.venv\Scripts\mcp-sentry.exe status
.\.venv\Scripts\mcp-sentry.exe doctor --manifest 'CAMINHO_DO_MANIFESTO' --store 'CAMINHO_DO_ESTADO'
```

Quando houver bloqueio, solicite ao cliente a revisão do Sentry. Em pedido
separado, solicite o registro do parecer. O modelo usa `review_token`,
`decision`, `justification` e `risks`; o recibo mostra o parecer persistido.
Registrar um parecer não autoriza execução.

## 4. Decidir sobre uma alteração

Após conferir o parecer, o operador decide em terminal:

```powershell
.\.venv\Scripts\mcp-sentry.exe review-update --manifest 'CAMINHO_DO_MANIFESTO' --store 'CAMINHO_DO_ESTADO' --action once
```

`once` autoriza um início de uso único. `--action accept` torna a versão
revisada referência permanente após confirmação. Alterações de configuração
ou política exigem promoção separada (`--action envelope`). Mudanças de
catálogo podem exigir descoberta (`--action catalog`) e nova revisão.

Esses comandos administrativos pertencem ao operador. Não os exponha como
ações automáticas do agente. O assistente não ativa aprovação pela conversa.

## 5. Atualizar uma instalação existente

Encerre as conexões que usam o Sentry. Extraia o pacote novo em outra pasta e
informe o ambiente da instalação anterior, sem movê-lo:

```powershell
.\instalar.ps1 -Ambiente 'C:\PASTA_DA_INSTALACAO_ANTERIOR\.venv' -SemConfigurar
```

O instalador atualiza o programa nesse ambiente e confere a versão. Não altera
manifestos, referências, pareceres, autorizações ou configuração do cliente.
Não repita `setup` para atualizar e não aprove novamente para ocultar uma
mudança pendente. Atualizar o gateway não aprova o MCP. Reinicie as conexões.

## 6. Restaurar a conexão anterior

O setup grava `codex-installation.json`. Para restaurar suas entradas:

```powershell
.\.venv\Scripts\mcp-sentry.exe restore-codex --installation-record 'CAMINHO\codex-installation.json'
.\.venv\Scripts\mcp-sentry.exe restore-codex --installation-record 'CAMINHO\codex-installation.json' --apply
```

A primeira chamada mostra a proposta; a segunda aplica com backup. Conflitos
com edições posteriores interrompem a aplicação. Estado, dados e pacotes não
são apagados. Reinicie as conexões. Instalações antigas sem esse registro
exigem restauração manual a partir de um backup conferido.

## O que mudou nesta entrega

A 1.1.0 reaproveita cópias verificadas e texto mascarado sob conferências
estritas e reduz trabalho repetido na leitura das evidências. O instalador
detecta Python, usa a identificação da versão, confere todos os arquivos e
oferece o setup. A decisão do operador e as ferramentas nativas são mantidas.

## Limites e ajuda

Protótipo Windows para ferramentas MCP locais via `stdio` e arquivos
declarados. Não cobre HTTP, recursos/prompts MCP, conexões diretas paralelas
ou todas as dependências externas automaticamente. Não é sandbox,
antivírus nem autenticação. A IA pode errar; aprovação de referência não
certifica segurança ou privacidade. O estado confiável deve ficar protegido
contra edição pelo agente.

`PRIVACIDADE.md` explica as regras de revisão. `SOLUCAO-DE-PROBLEMAS.md`
orienta os diagnósticos. `VERSAO.json` identifica wheel, fonte e validação
técnica da entrega; as baterias de modelo ficam separadas dessa validação.
