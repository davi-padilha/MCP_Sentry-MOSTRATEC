# Usar, atualizar e restaurar o MCP Sentry

## Abrir os comandos do programa instalado

Os exemplos abaixo usam a localização padrão de uma instalação nova.
Se o resumo mostrou outro ambiente, substitua o caminho de `$sentry`.
Abra PowerShell e defina:

```powershell
$sentry = Join-Path $env:LOCALAPPDATA 'MCP-Sentry-Gateway\.venv\Scripts\mcp-sentry.exe'
```

## Conectar um MCP

Com seu MCP local já funcionando no Codex:

```powershell
& $sentry setup
```

Selecione o servidor. Confira os arquivos e o catálogo antes de confirmar
descoberta, referência inicial e substituição da conexão. A descoberta inicia
uma cópia do MCP uma vez. A configuração recebe backup; o resumo mostra
manifesto, estado e `codex-installation.json`. Guarde esses caminhos.
Reinicie as conexões e confira execução e revisão separadas. Uma conexão
direta paralela do mesmo servidor continua fora da proteção.

Programa instalado e MCP conectado são etapas diferentes. O assistente
recusa formatos ainda não suportados; consulte [CONFIGURACAO.md](CONFIGURACAO.md).

## Conferir e usar

```powershell
& $sentry status
& $sentry doctor --manifest 'CAMINHO_DO_MANIFESTO' --store 'CAMINHO_DO_ESTADO'
```

Use as ferramentas normalmente. Se houver mudança, o Sentry bloqueia o
início da nova implementação. Solicite ao cliente a revisão do bloqueio e,
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
