# Usar, atualizar e restaurar o MCP Sentry

## Abrir os comandos do programa instalado

Os exemplos abaixo usam a localização padrão de uma instalação nova.
Se o resumo mostrou outro ambiente, substitua o caminho de `$sentry`.
Abra PowerShell e defina:

```powershell
$sentry = Join-Path $env:LOCALAPPDATA 'MCP-Sentry-Gateway\.venv\Scripts\mcp-sentry.exe'
```

## Conectar um MCP

Com seu MCP local já funcionando no cliente escolhido:

```powershell
& $sentry setup --client codex
# Para Claude Desktop:
& $sentry setup --client claude-desktop
```

Selecione o servidor. Confira os arquivos e o catálogo antes de confirmar
descoberta, referência inicial e substituição da conexão. A descoberta inicia
uma cópia do MCP uma vez. A configuração recebe backup; o resumo mostra
manifesto, estado e `codex-installation.json` ou `claude-desktop-installation.json`.
Guarde esses caminhos. No Claude Desktop, encerre completamente o aplicativo,
reabra e confira os dois conectores em uma conversa nova.
Reinicie as conexões e confira execução e revisão separadas. Uma conexão
direta paralela do mesmo servidor continua fora da proteção.

Programa instalado e MCP conectado são etapas diferentes. O assistente
recusa formatos ainda não suportados; consulte [CONFIGURACAO.md](CONFIGURACAO.md).

## Confirmar pelo chat ou pelo terminal

O modo padrão mantém as decisões de aprovação no terminal. Para configurar
um MCP novo com confirmação pelo chat, use `setup --client claude-desktop
--conversation-approval` (ou `--client codex`). O instalador também aceita
`-Configurar -Cliente claude-desktop -AprovarNoChat`. O modo confia no cliente
para atestar uma mensagem separada do usuário; não autentica sua identidade.
Em um MCP já preparado, não repita setup nem approve: acrescente
`--conversation-approval` aos argumentos das duas entradas, com backup,
e reconecte o cliente.

Depois de revisar e registrar um parecer favorável, o cliente deve distinguir:

- **Aceitar a versão:** nova mensagem `ACEITO ESTA VERSÃO COMO REFERÊNCIA PERMANENTE.`.
  O Sentry reconfere os hashes e atualiza a referência. A mesma versão permanece
  utilizável, inclusive após reconectar, e uma alteração posterior volta a bloquear.
- **Uma chamada de teste:** nova mensagem `APROVO UMA EXECUÇÃO DESTA VERSÃO.`.
  A permissão é consumida por uma chamada, inclusive uma prévia, sem aceitar a
  versão permanentemente. Outras chamadas continuam bloqueadas.

Uma resposta ambígua como “aprovado” deve gerar uma pergunta sobre qual opção
você deseja. Pedir revisão ou registro de parecer não confirma nenhuma delas.
Aceitar código não promove configuração, cobertura, política ou catálogo:
essas mudanças continuam exigindo preparação e decisão separadas do operador.
O aceite não inicia o servidor; a próxima ferramenta solicitada o inicia pela
cópia verificada. Confirmações de conteúdo exigidas pela Donna continuam separadas.

O registro e a aceitação recebem evidências obrigatórias. Mantenha o estado e
seus relatórios protegidos contra edição pelo agente. Ausência ou divergência
dos registros de aceitação impede executar a referência aceita pelo chat.

## Conferir e usar

```powershell
& $sentry status
# Para Claude Desktop:
& $sentry status --client claude-desktop
& $sentry doctor --manifest 'CAMINHO_DO_MANIFESTO' --store 'CAMINHO_DO_ESTADO'
```

Use as ferramentas normalmente. Se houver mudança, o Sentry bloqueia o
início da nova implementação. O cliente deve oferecer revisar a alteração
pelo conector separado de revisão, sem aprovar ou executar nada. Para pedir
essa análise, diga “Faça a revisão sugerida.”. Se esse conector não estiver
disponível, será necessário configurá-lo primeiro.
Solicite ao cliente a revisão do bloqueio e,
em outra mensagem, o registro do parecer. Registrar não autoriza execução.

Se concordar com um parecer favorável, o operador pode autorizar um início:

```powershell
& $sentry review-update --action once
```

O comando apresenta os servidores preparados, o parecer e a confirmação.
Também pode informar `--manifest` e `--store` explicitamente. `--action accept`
torna a versão referência permanente após confirmação. Mudanças de configuração
ou política exigem `--action envelope`; catálogo pode exigir `--action catalog`
e nova revisão. Não exponha esses comandos como ferramentas automáticas da IA.

Se a atualização também muda as ferramentas, use `--action catalog` depois
do parecer favorável. `DESCOBRIR` autoriza uma execução para consultar o catálogo;
confira o resultado antes de `APLICAR_CATALOGO`. Essa aplicação exige nova
revisão e parecer antes de autorizar o uso da versão.

## Atualizar uma instalação

Encerre as conexões que usam o Sentry. Extraia o ZIP novo inteiro e abra
PowerShell na pasta extraída. Para atualizar a instalação padrão:

```powershell
.\arquivos-instalacao\instalar.ps1 -SemConfigurar
```

Para uma instalação antiga ou em outro caminho, informe sua `.venv` existente:

```powershell
.\arquivos-instalacao\instalar.ps1 -Ambiente 'C:\PASTA_ANTERIOR\.venv' -SemConfigurar
```

O ambiente é atualizado no mesmo lugar. Manifestos, referências, pareceres,
autorizações e configuração do cliente são preservados. Não repita o setup
ou a aprovação inicial para atualizar. Reinicie as conexões ao terminar.

O instalador reconhece uma `.venv` antiga na raiz da pasta extraída e a mantém.
Ele não move automaticamente ambientes já conectados a clientes. Na instalação
padrão nova, a pasta extraída pode ser removida depois; em instalações antigas
que guardam a `.venv` nela, preserve a pasta do ambiente.

## Instalar sem o lançador ou escolher outro Python

Na pasta extraída:

```powershell
.\arquivos-instalacao\instalar.ps1 -SemConfigurar
.\arquivos-instalacao\instalar.ps1 -PythonExe 'C:\CAMINHO\python.exe'
.\arquivos-instalacao\instalar.ps1 -Configurar
```

Se PowerShell impedir scripts, confira o hash do wheel em
`arquivos-instalacao/SHA256SUMS.txt` e use Python diretamente. Leia o nome
do wheel em `arquivos-instalacao/VERSAO.json`:

```powershell
$versao = Get-Content .\arquivos-instalacao\VERSAO.json -Raw | ConvertFrom-Json
$ambiente = Join-Path $env:LOCALAPPDATA 'MCP-Sentry-Gateway\.venv'
py -3 -m venv $ambiente
& (Join-Path $ambiente 'Scripts\python.exe') -m pip install --no-index --no-deps (Join-Path '.\arquivos-instalacao' $versao.wheel)
```

Essa alternativa é para uma instalação nova em pasta vazia. Para atualizar,
use o Python do ambiente existente com o novo wheel; não recrie sua `.venv`.
Troque `py -3` pelo executável de Python se o launcher não estiver disponível.
Não altere permanentemente a política global do PowerShell só para instalar.

## Restaurar a conexão anterior

Use o registro apresentado pelo setup:

```powershell
& $sentry restore-codex --installation-record 'CAMINHO\codex-installation.json'
& $sentry restore-codex --installation-record 'CAMINHO\codex-installation.json' --apply
# Para Claude Desktop, primeiro veja a proposta e depois aplique:
& $sentry restore-claude-desktop --installation-record 'CAMINHO\claude-desktop-installation.json'
& $sentry restore-claude-desktop --installation-record 'CAMINHO\claude-desktop-installation.json' --apply
```

A primeira chamada mostra a proposta; a segunda aplica com backup. Edições
conflitantes são preservadas. Reinicie as conexões. Dados, estado e pacotes
não são apagados. Instalações antigas sem registro exigem comparar o backup
manualmente antes de restaurar suas entradas.

## Limites

Protótipo Windows para ferramentas MCP locais por `stdio` e arquivos
declarados. Não cobre HTTP, recursos/prompts MCP ou dependências externas
automaticamente. A IA pode errar a revisão. Referência aprovada não certifica
segurança ou privacidade. Proteja o estado contra edição pelo agente.
As somas verificam os bytes recebidos, sem autenticar seu remetente.
