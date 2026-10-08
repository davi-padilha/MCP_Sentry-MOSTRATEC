# Configuração manual e referência de operação

Use o README.md para instalar a versão 1.0.0. Esta referência cobre preparo manual, outros clientes stdio, decisões e limites.

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
      "command": "C:\\caminho\\desenvolvimento\gateway\\.venv\\Scripts\\mcp-sentry-gateway.exe",
      "args": ["--interface", "execution", "--manifest", "C:\\MCP\\config\\meu-servidor.json", "--store", "C:\\caminho\\estado"]
    },
    "mcp_sentry_review": {
      "command": "C:\\caminho\\desenvolvimento\gateway\\.venv\\Scripts\\mcp-sentry-gateway.exe",
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

## Operação da versão 1.0.0

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
