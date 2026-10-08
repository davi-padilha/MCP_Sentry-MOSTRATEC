# Instalar o MCP Sentry 1.0

Esta é a pasta que você precisa receber para instalar o MCP Sentry.
O gateway protege ferramentas de um servidor MCP local iniciado por `stdio`:
confere código e configuração contra uma referência aprovada e bloqueia
alterações até revisão e decisão do operador.

## Antes de começar

- Windows com Python 3.11 ou posterior. A validação desta distribuição registra
  a versão efetivamente usada em `VERSAO.json`; outras versões não têm a mesma
  evidência de teste.
- Seu servidor MCP e seu runtime (Python ou Node), funcionando separadamente.
- Um cliente de IA com servidores MCP locais. A configuração assistida é
  para Codex; outros clientes usam a configuração manual.
- Suas próprias credenciais e dados, quando o seu MCP os exigir.

O pacote contém o gateway, não Python, o MCP protegido ou credenciais.
Não é necessário baixar o restante do repositório. Instale em um caminho
estável, fora da pasta de código do servidor e das raízes graváveis do agente.

## 1. Instalar

Abra PowerShell nesta pasta e execute:

```powershell
.\instalar.ps1
```

O script verifica o wheel contra `SHA256SUMS.txt`, cria `.venv` e instala
o pacote local. Não inicia seu MCP nem altera a configuração do cliente.
Se `py` não estiver disponível, informe o executável do Python:

```powershell
.\instalar.ps1 -PythonExe 'C:\CAMINHO\python.exe'
```

Se a política local impedir scripts, use a instalação manual abaixo, sem
alterar permanentemente a política do Windows:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps .\mcp_sentry_gateway-1.0.0-py3-none-any.whl
```

Confira o hash com `Get-FileHash` antes da instalação manual. O hash detecta
mudança em relação ao arquivo de somas recebido; não autentica o remetente.

## 2. Conectar seu MCP no Codex

Com o MCP já configurado diretamente no Codex:

```powershell
.\.venv\Scripts\mcp-sentry.exe setup
```

O assistente apresenta as entradas locais suportadas, os arquivos e o catálogo.
Ele pede confirmações distintas para descobrir as ferramentas, aprovar a
referência inicial e substituir a conexão direta. A descoberta inicia o MCP
uma vez; use apenas código que você autorizou executar. Configuração alterada
recebe backup. Anote os caminhos do manifesto, estado e registro de instalação.

Entradas Python/Node locais e formatos suportados de `npx`/`uvx` podem ser
preparados pelo assistente. Instalações de pacotes do MCP podem exigir internet.
Opções incompatíveis são recusadas para preservar a configuração original.
O setup não suporta todo formato de launcher. Para preparação manual ou
outros clientes, consulte [CONFIGURACAO.md](CONFIGURACAO.md).

Reinicie as conexões do Codex. Confira que a execução passa pelo Sentry e
que a interface de revisão separada está disponível. Desative conexões diretas
paralelas do mesmo MCP: elas não recebem a proteção do gateway.

## 3. Usar e conferir

Use as ferramentas do seu MCP normalmente. Com a referência inalterada,
argumentos e respostas nativas são preservados. Uma alteração provoca bloqueio
antes do início da nova implementação.

```powershell
.\.venv\Scripts\mcp-sentry.exe status
```

Para conferir uma configuração salva:

```powershell
.\.venv\Scripts\mcp-sentry.exe doctor --manifest 'CAMINHO_DO_MANIFESTO' --store 'CAMINHO_DO_ESTADO'
```

Quando houver bloqueio, solicite ao seu cliente de IA a revisão do Sentry.
Depois, em pedido separado, solicite o registro do parecer. O modelo usa
`review_token`, `decision`, `justification` e `risks`; o recibo informa o
parecer realmente persistido. Campo ausente recebe instruções de correção.
Registro de parecer não autoriza execução.

## 4. Decidir sobre uma alteração

A decisão padrão é feita pelo operador em terminal, após conferir o parecer:

```powershell
.\.venv\Scripts\mcp-sentry.exe review-update --manifest 'CAMINHO_DO_MANIFESTO' --store 'CAMINHO_DO_ESTADO' --action once
```

`once` autoriza um início de uso único. `--action accept` torna a versão
revisada referência permanente após confirmação. Mudanças de configuração
de execução ou de política exigem uma promoção separada (`--action envelope`).
Mudanças de catálogo podem exigir descoberta (`--action catalog`) seguida
de nova revisão. Confira o que é apresentado antes de confirmar.

Não exponha esses comandos administrativos como ações automáticas do agente.
O modo experimental de aprovação pela conversa é opcional, confia na atestação
do cliente e não autentica a autoria humana. A instalação assistida não o ativa.

## 5. Atualizar ou restaurar a conexão anterior

Para atualizar uma instalação existente, execute o Python daquela instalação
com `-m pip install --no-deps` apontando ao novo wheel. Preserve o caminho
do ambiente, manifesto e estado. Não repita a aprovação inicial para ocultar
uma atualização pendente. Atualizar o gateway não aprova seu MCP.

O setup grava `codex-installation.json`. Para restaurar somente as entradas
que ele substituiu:

```powershell
.\.venv\Scripts\mcp-sentry.exe restore-codex --installation-record 'CAMINHO\codex-installation.json'
.\.venv\Scripts\mcp-sentry.exe restore-codex --installation-record 'CAMINHO\codex-installation.json' --apply
```

A primeira chamada apresenta a proposta; a segunda aplica com backup.
Edições conflitantes são preservadas como conflito. Reinicie as conexões após
restaurar. Estado, dados e pacotes não são apagados. Instalações antigas sem
registro exigem restauração manual a partir do backup conferido.

## Limites e ajuda

A 1.0 é a primeira distribuição validada do protótipo neste escopo. Protege
arquivos declarados e ferramentas locais via `stdio`. Não cobre HTTP,
recursos/prompts MCP, conexões diretas paralelas nem todas as dependências
externas automaticamente. Não é sandbox, antivírus ou autenticação.
O modelo pode errar a análise; aprovação de referência não certifica segurança
ou privacidade. Estado confiado deve ficar indisponível para edição pelo agente.

[PRIVACIDADE.md](PRIVACIDADE.md) explica as regras de revisão.
[SOLUCAO-DE-PROBLEMAS.md](SOLUCAO-DE-PROBLEMAS.md) explica os problemas comuns.
`VERSAO.json` identifica o pacote e a validação técnica. Os resultados das
baterias de modelo são registrados separadamente, com sua versão e configuração.
