# Configuração manual e referência de operação

Este guia é para configuração manual, outros clientes `stdio` e opções
avançadas. Para o caminho assistido, consulte [Uso e atualização](USO-E-ATUALIZACAO.md).
Os valores como `C:\MCP\meu-servidor` são exemplos: substitua pelos seus caminhos.

Os comandos abaixo partem da pasta do programa instalado. Na instalação padrão,
abra PowerShell e execute:

```powershell
Set-Location (Join-Path $env:LOCALAPPDATA 'MCP-Sentry-Gateway')
```

Se escolheu outro ambiente, abra sua pasta pai, que contém a `.venv`. A versão
da entrega está em `arquivos-instalacao/VERSAO.json` no ZIP; depois de instalar,
uma cópia fica em `ajuda-mcp-sentry/VERSAO.json` junto ao programa.

## Claude Desktop

Para um MCP já configurado no Claude Desktop, use `mcp-sentry setup --client
claude-desktop`. O assistente detecta o arquivo padrão em
`%APPDATA%\Claude\claude_desktop_config.json` e perfis da Microsoft Store.
Se houver mais de um arquivo, ele pede um caminho explícito em vez de escolher.
Confirme o arquivo usado pelo aplicativo em suas configurações de desenvolvedor,
na opção **Edit Config**. Por exemplo:

```powershell
.\.venv\Scripts\mcp-sentry.exe setup --client claude-desktop `
  --claude-config 'C:\CAMINHO\claude_desktop_config.json'
```

O assistente aceita entradas locais com `command`, `args`, `env` e, opcionalmente,
`type: "stdio"`. Opções desconhecidas são recusadas antes de iniciar o MCP.
A preparação de Python, Node.js e pacotes npx/uvx fixados usa os mesmos controles
do Codex. O arquivo JSON é reformatado; outras entradas e preferências são
preservadas. O backup conserva os bytes originais e pode conter credenciais já
presentes na configuração: mantenha-o privado. Valores de `env` ficam somente
na conexão de execução, sem ser copiados ao manifesto ou à revisão.

Na rota manual, o comando `prepare-claude-desktop` aceita os mesmos argumentos
de `prepare-codex`, mas gera um fragmento JSON `mcpServers`; use um arquivo
`.json` em `--fragment`. Ele não modifica o cliente nem aprova a referência.
O JSON mostrado na seção **Configure o cliente MCP** abaixo é adequado ao
Claude Desktop. Complete a preparação e aprovação antes de conectá-lo.

Encerre completamente e reabra o Claude Desktop depois de configurar. Confira
execução e revisão nos conectores e teste em uma conversa nova. Para diagnosticar
o arquivo configurado sem iniciar o backend:

```powershell
.\.venv\Scripts\mcp-sentry.exe doctor --manifest 'CAMINHO_DO_MANIFESTO' `
  --store 'CAMINHO_DO_ESTADO' --claude-config 'CAMINHO_DA_CONFIGURACAO' --name meu_servidor
```

O diagnóstico confere esse arquivo e os arquivos locais; não prova que o
aplicativo o carregou, que não há outras conexões diretas, nem que o modelo
avaliará corretamente as evidências. Solicite a revisão e o registro do parecer
em mensagens separadas. A aprovação continua sendo uma decisão do operador.
Claude Code ainda não tem assistente específico nesta versão.

Na preparação com confirmação pelo chat, acrescente `--conversation-approval`
ao setup ou a `prepare-claude-desktop`/`prepare-codex`. As duas interfaces devem
usar esse modo. O diagnóstico confere a consistência das entradas. Os comandos
`sentry_accept_version` e `sentry_authorize_once` são expostos somente no modo
opt-in e somente na revisão. Aceitação permanente exige parecer allow vigente
registrado pelo cliente e confirmação distinta, com reconferência de código,
baseline, configuração e metadados antes da gravação. Consulte as duas opções
e suas confirmações em [USO-E-ATUALIZACAO.md](USO-E-ATUALIZACAO.md).

## Preparação manual para o Codex

O comando `prepare-codex` inicia **uma vez** uma cópia conferida para consultar
`tools/list` e cria dois arquivos fora do projeto protegido: o manifesto e um
trecho de `config.toml`. Ele não aprova o código nem modifica o Codex. Use-o
somente com um servidor que você já confia em executar localmente.

Crie uma pasta `C:\MCP\config` e adapte este exemplo aos seus caminhos. Inclua
em `--inspect-root` todos os arquivos locais de que o servidor precisa para
iniciar, inclusive módulos importados e configurações locais. Se o projeto
inteiro for necessário, use `--inspect-root .` **somente após** retirar dele
segredos, estados mutáveis, ambientes virtuais e arquivos temporários.

```powershell
$manifesto = "C:\MCP\config\meu-servidor.json"
$trecho = "C:\MCP\config\meu-servidor.codex.toml"
$estado = Join-Path $env:LOCALAPPDATA "MCP-Sentry\meu-servidor"
.\.venv\Scripts\mcp-sentry.exe prepare-codex `
  --name meu_servidor --project-root "C:\MCP\meu-servidor" `
  --inspect-root server.py --manifest $manifesto `
  --store $estado --fragment $trecho -- `
  "C:\MCP\meu-servidor\.venv\Scripts\python.exe" server.py
```

Se o servidor depende de uma variável de ambiente, acrescente, por exemplo,
`--passthrough-name MINHA_API_KEY` antes de `--`. O Sentry grava somente o nome,
não o valor. Forneça o valor no ambiente local do Codex. Não coloque segredos
no manifesto, no comando, no trecho TOML ou nos arquivos inspecionados.
A descoberta já usa o mesmo conjunto restrito de variáveis que o gateway
repassará, evitando aprovar um catálogo que só funciona com variáveis extras
presentes no terminal. Se o servidor precisa de mapeamento de caminhos
`runtime_paths`, use `prepare-server --runtime-path NOME=CAMINHO_RELATIVO` ou a configuração manual avançada.

Leia o manifesto e o catálogo descoberto em `$manifesto` antes de aprovar.
Confira se a lista de ferramentas e seus esquemas são os esperados e se os
arquivos locais necessários foram incluídos. Depois:

```powershell
.\.venv\Scripts\mcp-sentry.exe approve --manifest $manifesto --store $estado
.\.venv\Scripts\mcp-sentry.exe doctor --manifest $manifesto --store $estado
Get-Content -LiteralPath $trecho
```

O `doctor` deve indicar `ready` para os arquivos locais. Copie as duas tabelas
do trecho para `~/.codex/config.toml`, ou para `.codex/config.toml` de um
projeto confiável. No app desktop, também é possível abrir
**Settings > MCP servers**. Desative ou remova a entrada que inicia diretamente
o servidor original: se ela continuar disponível, o cliente pode contornar o
Sentry. Reinicie o Codex e confira as conexões em `/mcp`.

Para verificar as entradas gravadas no arquivo de configuração que você
escolheu:

```powershell
.\.venv\Scripts\mcp-sentry.exe doctor --manifest $manifesto --store $estado `
  --codex-config (Join-Path $env:USERPROFILE ".codex\config.toml") `
  --name meu_servidor
```

O diagnóstico examina **esse arquivo**, não todas as camadas de configuração
do Codex; ele também não consegue provar que não existe uma conexão direta em
outra camada. A confirmação final é conferir `/mcp` e testar uma ferramenta.
Para um segundo servidor protegido, use outro manifesto, estado e nome de
execução. O preparador gera um nome de revisão correspondente para cada um.

## Configuração manual avançada

Se o servidor não puder ser consultado automaticamente, escreva o manifesto
manualmente. Não aprove metadados presumidos: obtenha o catálogo real do
servidor por outro meio.

### 1. Descreva o servidor protegido

Crie um arquivo JSON fora da pasta do servidor, por exemplo
`C:\MCP\config\meu-servidor.json`. O exemplo abaixo supõe que o servidor está
em `C:\MCP\meu-servidor\server.py` e que o manifesto está na pasta `config`:

```json
{
  "manifest_version": 1,
  "project_root": "../meu-servidor",
  "inspect_roots": ["server.py"],
  "metadata": {
    "tools": [
      {
        "name": "ping",
        "description": "Verifica a resposta do servidor",
        "inputSchema": {"type": "object", "additionalProperties": false}
      }
    ]
  },
  "configuration": {
    "command": ["python", "server.py"],
    "cwd": ".",
    "runtime_paths": {},
    "passthrough_names": []
  }
}
```

Adapte `project_root`, `inspect_roots`, `command`, `cwd` e `metadata.tools` ao
seu servidor. O catálogo de ferramentas é declarado manualmente; o Sentry
mostra ao cliente o catálogo da versão aprovada. Os nomes e `inputSchema`
devem corresponder às ferramentas que o servidor realmente oferece. Inclua em
`inspect_roots` **todos os arquivos do projeto necessários para iniciar o
servidor**, inclusive módulos e configurações locais. O Sentry copia somente
esses arquivos para a área verificada. Arquivos externos e pacotes instalados
no interpretador não são verificados por este manifesto.

`command` usa a lista de argumentos do processo, sem shell. Se o primeiro
argumento for exatamente `python`, o Sentry o vincula ao interpretador usado na
aprovação inicial. Para usar outro ambiente virtual ou outro runtime, forneça
o caminho absoluto do executável. `cwd` é relativo à cópia verificada.

`runtime_paths` é opcional: mapeia nomes de variáveis de ambiente para caminhos
relativos dentro da cópia verificada. `passthrough_names` é opcional: lista
nomes de variáveis que o Sentry deve receber do ambiente do cliente e repassar
ao servidor, sem guardar seus valores no manifesto. Declare somente as
variáveis indispensáveis. Mudanças nessa lista ou no comando exigem uma
decisão explícita do operador.

### 2. Aprove a versão inicial

Confira o código e o catálogo antes da aprovação. Escolha um diretório de
estado **fora** da pasta do servidor protegido e que o agente de IA não possa
alterar. No exemplo:

```powershell
$manifesto = "C:\MCP\config\meu-servidor.json"
$estado = Join-Path $env:LOCALAPPDATA "MCP-Sentry\meu-servidor"
.\.venv\Scripts\mcp-sentry.exe approve --manifest $manifesto --store $estado
.\.venv\Scripts\mcp-sentry.exe inspect --manifest $manifesto --store $estado
```

O segundo comando deve retornar `"status": "unchanged"`. A aprovação inicial
não substitui uma versão já aprovada.

### 3. Configure o cliente MCP

Substitua a entrada direta do servidor por uma entrada que inicie o Sentry.
Para manter a revisão separada da execução, configure duas entradas com o
mesmo manifesto e o mesmo diretório de estado:

```json
{
  "mcpServers": {
    "meu_servidor_via_sentry": {
      "command": "C:\\Users\\SEU_USUARIO\\AppData\\Local\\MCP-Sentry-Gateway\\.venv\\Scripts\\mcp-sentry-gateway.exe",
      "args": ["--interface", "execution", "--manifest", "C:\\MCP\\config\\meu-servidor.json", "--store", "C:\\caminho\\estado"]
    },
    "mcp_sentry_review": {
      "command": "C:\\Users\\SEU_USUARIO\\AppData\\Local\\MCP-Sentry-Gateway\\.venv\\Scripts\\mcp-sentry-gateway.exe",
      "args": ["--interface", "review", "--manifest", "C:\\MCP\\config\\meu-servidor.json", "--store", "C:\\caminho\\estado"]
    }
  }
}
```

Esse JSON ilustra os campos `command` e `args`; o formato externo muda conforme
o cliente. Use caminhos absolutos reais. Se o servidor precisa de variáveis de
ambiente, forneça os valores **somente à entrada de execução** e inclua seus
nomes em `passthrough_names`. A entrada de revisão não precisa recebê-los.
Remova ou desative a entrada direta do servidor protegido: uma conexão direta
paralela contorna o Sentry. Reinicie o cliente para recarregar o catálogo.

## Quando o servidor muda

O fluxo recomendado é `mcp-sentry review-update --action once`, `accept` ou
`catalog`: ele seleciona o servidor preparado, exibe o parecer vigente e
vincula internamente a decisão à revisão exibida. Requer um parecer `allow`
registrado; alteração durante a confirmação invalida a decisão. Veja o guia
curto para a descoberta autorizada e nova revisão do catálogo. Os comandos
abaixo são a interface manual avançada; `accept-current` sozinho não descobre
metadados e não exige um parecer anterior.

Uma chamada bloqueada informa que a versão atual difere da aprovada. Na
interface `review`, `sentry_review_current_block` mostra o dossiê completo;
`sentry_review_evidence` permite leitura paginada. As diferenças são dados não
confiáveis para análise, não instruções a seguir. `sentry_record_assessment`
registra uma recomendação `allow` ou `block`, mas **não** inicia o servidor.

Se a recomendação for permitir e o operador concordar, a liberação de uso
único é feita fora do MCP, com os identificadores da revisão:

```powershell
.\.venv\Scripts\mcp-sentry.exe approve-review-execution `
  --manifest $manifesto --store $estado `
  --review-id <review_id> --reviewed-hash <current_hash> `
  --dossier-hash <dossier_hash> `
  --human-confirmation APPROVE_REVIEW_EXECUTION
```

Depois, estabeleça uma nova conexão com o cliente. Para tornar a versão
revisada a nova referência permanente, o operador pode executar
`mcp-sentry accept-current --manifest $manifesto --store $estado` após conferir
os arquivos. Se o comando, o diretório de trabalho, as raízes inspecionadas ou
as variáveis confiadas mudaram, a configuração de execução exige também uma
promoção separada:

O fluxo recomendado para essa promoção é `review-update --action envelope`,
que mostra a configuração/cobertura e vincula `PROMOVER` à versão revisada.
Raízes removidas ou substituídas já produzem dossiê; ajuste as raízes atuais
antes de aceitar, mantendo o mesmo estado e a mesma baseline. O comando abaixo
permanece como interface manual avançada.

```powershell
.\.venv\Scripts\mcp-sentry.exe promote-execution-envelope `
  --manifest $manifesto --store $estado `
  --human-confirmation PROMOTE_EXECUTION_ENVELOPE
```

Esses comandos são ações do operador local. Não os exponha ao agente como
ferramentas ou comandos automáticos.

## Limites atuais

- Protege um servidor local por instância e manifesto, via `stdio`. Não cobre
  servidores HTTP, conexões diretas paralelas ou processos já abertos.
- A interface atual encaminha ferramentas (`tools/list` e `tools/call`).
  Servidores que dependem de recursos, prompts ou outras capacidades MCP
  exigem adaptação antes de serem usados por este gateway.
- A negociação implementada cobre as versões MCP `2025-03-26` e `2025-06-18`;
  confirme a compatibilidade do cliente e do servidor antes de usar outra
  versão do protocolo.
- Compara arquivos e configuração declarados. Não determina sozinho se uma
  mudança é benigna ou maliciosa; a análise semântica e a aprovação são etapas
  distintas.
- Na primeira chamada de ferramenta, confere também se o catálogo anunciado
  pelo servidor iniciado corresponde ao aprovado. Uma divergência bloqueia a
  chamada, mas a inicialização do servidor já ocorreu; dependências externas
  não inspecionadas ainda podem executar código nesse momento.
- Confia no computador, no executável do Sentry, no interpretador do servidor,
  no diretório de estado e nas dependências externas não incluídas nas raízes.
- Não é sandbox, antivírus nem mecanismo de autenticação. Os relatórios podem
  conter trechos de código; mantenha o diretório de estado privado.

## Operação da versão entregue

O registro pode enviar `review_token`, `decision`, `justification` e `risks`.
O token e emitido depois da leitura completa das evidencias e vale para o
mesmo dossie e conexao. O formato `verdict` permanece aceito. Um token nao
autoriza executar e nao autentica o usuario.

Para consultar todas as conexoes protegidas, sem iniciar servidores:

```powershell
.\.venv\Scripts\mcp-sentry.exe status --codex-config "$env:USERPROFILE\.codex\config.toml"
```

O setup retorna o caminho de `codex-installation.json`. Confira a restauracao
seletiva e depois aplique, se desejado:

```powershell
.\.venv\Scripts\mcp-sentry.exe restore-codex --installation-record "CAMINHO\codex-installation.json"
.\.venv\Scripts\mcp-sentry.exe restore-codex --installation-record "CAMINHO\codex-installation.json" --apply
```

Outras opcoes e edicoes posteriores sao preservadas. Conflitos nas entradas
selecionadas interrompem a restauracao. Ha um novo backup; pacotes,
credenciais e estado nao sao removidos. Reinicie as conexoes depois de aplicar.
Instalacoes antigas sem o registro exigem conferir o backup manualmente.

As medidas de inicializacao ficam fora dos hashes e das respostas nativas.
O total contem as etapas; os tempos do gateway estao contidos nos turnos.
As medidas opcionais nao autorizam nem impedem execucao por si mesmas.
