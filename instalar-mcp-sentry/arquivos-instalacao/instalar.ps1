[CmdletBinding()]
param(
    [string]$PythonExe,
    [string]$Ambiente,
    [switch]$Configurar,
    [switch]$SemConfigurar,
    [switch]$AprovarNoChat,
    [string]$CodexConfig,
    [string]$ClaudeConfig,
    [ValidateSet('codex','claude-desktop')][string]$Cliente,
    [string]$StateRoot
)
$ErrorActionPreference = 'Stop'
if ($Configurar -and $SemConfigurar) { throw 'Escolha -Configurar ou -SemConfigurar.' }
if ($AprovarNoChat -and !$Configurar) { throw '-AprovarNoChat exige -Configurar.' }
if (($CodexConfig -or $ClaudeConfig -or $Cliente -or $StateRoot) -and !$Configurar) { throw '-Cliente, -CodexConfig, -ClaudeConfig e -StateRoot exigem -Configurar.' }
if ($CodexConfig -and $ClaudeConfig) { throw 'Escolha apenas uma configuracao de cliente.' }
if ($CodexConfig -and $Cliente -and $Cliente -ne 'codex') { throw '-CodexConfig requer -Cliente codex.' }
if ($ClaudeConfig -and $Cliente -and $Cliente -ne 'claude-desktop') { throw '-ClaudeConfig requer -Cliente claude-desktop.' }
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskDataRoot = $PSScriptRoot

function Get-TaskHash([string]$Path) {
    $taskStream = [System.IO.File]::OpenRead($Path)
    $taskHasher = [System.Security.Cryptography.SHA256]::Create()
    try { return ([System.BitConverter]::ToString($taskHasher.ComputeHash($taskStream))).Replace('-','').ToLowerInvariant() }
    finally { $taskStream.Dispose(); $taskHasher.Dispose() }
}

# Check every distributed file before trusting its version or running Python.
$taskSums = @{}
foreach ($taskLine in (Get-Content -LiteralPath (Join-Path $taskDataRoot 'SHA256SUMS.txt'))) {
    if ($taskLine -notmatch '^([0-9a-f]{64})  ((?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]+)$') { throw 'Lista de somas invalida.' }
    $taskHash = $Matches[1]; $taskName = $Matches[2]
    if ($taskSums.ContainsKey($taskName)) { throw 'Nome repetido na lista de somas.' }
    $taskPath = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskName))
    if (!$taskPath.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or @($taskName.Split('/') | Where-Object { $_ -eq '.' -or $_ -eq '..' }).Count) { throw 'Caminho invalido na lista de somas.' }
    if (!(Test-Path -LiteralPath $taskPath -PathType Leaf) -or (Get-TaskHash $taskPath) -ne $taskHash) {
        throw "Arquivo ausente ou diferente da soma recebida: $taskName. Obtenha novamente a distribuicao."
    }
    $taskSums[$taskName] = $taskHash
}
foreach ($taskName in @('README.md','INSTALAR.cmd','arquivos-instalacao/VERSAO.json','arquivos-instalacao/instalar.ps1','ajuda/README.md','ajuda/USO-E-ATUALIZACAO.md','ajuda/CONFIGURACAO.md','ajuda/PRIVACIDADE.md','ajuda/SOLUCAO-DE-PROBLEMAS.md')) {
    if (!$taskSums.ContainsKey($taskName)) { throw "Soma obrigatoria ausente: $taskName." }
}
$taskMetadata = Get-Content -LiteralPath (Join-Path $taskDataRoot 'VERSAO.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskVersion = [string]$taskMetadata.versao
$taskMinimum = [string]$taskMetadata.python_minimo
if ($taskVersion -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$' -or $taskMinimum -notmatch '^[0-9]+\.[0-9]+$') { throw 'Versao ou requisito Python invalido em VERSAO.json.' }
$taskWheelName = "mcp_sentry_gateway-$taskVersion-py3-none-any.whl"
$taskWheelEntry = 'arquivos-instalacao/' + $taskWheelName
if ($taskMetadata.wheel -ne $taskWheelName -or !$taskSums.ContainsKey($taskWheelEntry) -or $taskMetadata.wheel_sha256 -ne $taskSums[$taskWheelEntry]) {
    throw 'Wheel, versao e somas nao correspondem.'
}
$taskWheel = Join-Path $taskDataRoot $taskWheelName
if (!$Ambiente) {
    $taskLegacy = Join-Path $taskRoot '.venv'
    if (Test-Path -LiteralPath (Join-Path $taskLegacy 'Scripts/python.exe')) {
        $Ambiente = $taskLegacy
        Write-Output 'Instalacao anterior nesta pasta detectada. Seu caminho sera preservado.'
    } else {
        if (!$env:LOCALAPPDATA) { throw 'LOCALAPPDATA nao definido. Informe uma pasta com -Ambiente.' }
        $Ambiente = Join-Path $env:LOCALAPPDATA 'MCP-Sentry-Gateway/.venv'
    }
}
$taskEnvironment = [System.IO.Path]::GetFullPath($Ambiente)
$taskVenvPython = Join-Path $taskEnvironment 'Scripts/python.exe'
$taskPrevious = $null

function Get-TaskPython([string]$Command, [string[]]$PrefixArgs = @()) {
    $taskProbe = "import sys,json,importlib.util; print(json.dumps(dict(executable=sys.executable,version=list(sys.version_info[:3]),venv=importlib.util.find_spec('venv') is not None,ensurepip=importlib.util.find_spec('ensurepip') is not None)))"
    try {
        $taskOutput = @(& $Command @PrefixArgs -I -c $taskProbe 2>&1)
        if ($LASTEXITCODE -ne 0) { return $null }
        $taskInfo = $taskOutput[-1] | ConvertFrom-Json
        $taskFound = [version]($taskInfo.version -join '.')
        if ($taskFound -lt [version]$taskMinimum -or !$taskInfo.venv -or !$taskInfo.ensurepip -or !(Test-Path -LiteralPath $taskInfo.executable -PathType Leaf)) { return $null }
        return $taskInfo
    } catch { return $null }
}

if (Test-Path -LiteralPath $taskVenvPython -PathType Leaf) {
    $taskPython = Get-TaskPython $taskVenvPython
    if (!$taskPython) { throw "O ambiente existente nao tem Python $taskMinimum+ utilizavel. Preserve-o e informe outro -Ambiente; nao sera recriado automaticamente." }
    $taskPreviousOutput = @(& $taskVenvPython -I -c "import importlib.metadata as m; print(next((d.version for d in m.distributions() if d.metadata['Name']=='mcp-sentry-gateway'), ''))" 2>$null)
    if ($LASTEXITCODE -eq 0) { $taskPrevious = [string]$taskPreviousOutput[-1] }
} else {
    if (Test-Path -LiteralPath $taskEnvironment) { throw "O ambiente existente nao tem um executavel Python utilizavel: $taskEnvironment. Preserve-o e escolha outra pasta com -Ambiente." }
    $taskPython = $null
    if ($PythonExe) {
        $taskPython = Get-TaskPython $PythonExe
        if (!$taskPython) { throw "O Python informado nao funciona ou nao atende Python $taskMinimum+ com venv e ensurepip: $PythonExe." }
    } else {
        $taskCandidates = @()
        $taskLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($taskLauncher) { $taskPython = Get-TaskPython $taskLauncher.Source @('-3') }
        foreach ($taskCommand in @('python.exe','python3.exe')) {
            $taskResolved = Get-Command $taskCommand -ErrorAction SilentlyContinue
            if ($taskResolved) { $taskCandidates += $taskResolved.Source }
        }
        foreach ($taskPattern in @("$env:LOCALAPPDATA\Python\pythoncore-*\python.exe", "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe")) {
            $taskCandidates += @(Get-ChildItem -Path $taskPattern -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -ExpandProperty FullName)
        }
        foreach ($taskRegistry in @('HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore', 'HKLM:\Software\WOW6432Node\Python\PythonCore')) {
            foreach ($taskKey in @(Get-ChildItem -LiteralPath $taskRegistry -ErrorAction SilentlyContinue)) {
                $taskInstallKey = Get-Item -LiteralPath (Join-Path $taskKey.PSPath 'InstallPath') -ErrorAction SilentlyContinue
                if ($taskInstallKey) {
                    $taskRegistered = $taskInstallKey.GetValue('ExecutablePath')
                    if (!$taskRegistered -and $taskInstallKey.GetValue('')) { $taskRegistered = Join-Path $taskInstallKey.GetValue('') 'python.exe' }
                    if ($taskRegistered) { $taskCandidates += $taskRegistered }
                }
            }
        }
        foreach ($taskCandidate in @($taskCandidates | Select-Object -Unique)) {
            if ($taskPython) { break }
            $taskPython = Get-TaskPython $taskCandidate
        }
        if (!$taskPython) { throw "Python $taskMinimum+ nao encontrado. Instale Python com venv/pip (https://www.python.org/downloads/windows/) ou execute .\arquivos-instalacao\instalar.ps1 -PythonExe 'C:\CAMINHO\python.exe'. Atalhos da Microsoft Store nao comprovam uma instalacao utilizavel." }
    }
    Write-Output "Python encontrado: $($taskPython.executable) ($($taskPython.version -join '.'))."
    & $taskPython.executable -I -m venv $taskEnvironment
    if ($LASTEXITCODE -ne 0) { throw "Falha ao criar o ambiente em $taskEnvironment. Confira permissoes e espaco em disco." }
}

Write-Output "Instalando MCP Sentry $taskVersion em $taskEnvironment..."
& $taskVenvPython -I -m pip --isolated --disable-pip-version-check install --no-index --no-deps $taskWheel
if ($LASTEXITCODE -ne 0) { throw 'Instalacao nao concluida. Preserve o ambiente e consulte ajuda/SOLUCAO-DE-PROBLEMAS.md.' }
@'
import importlib.metadata, sys
import mcp_sentry_gateway
expected = sys.argv[1]
assert importlib.metadata.version('mcp-sentry-gateway') == expected
assert mcp_sentry_gateway.__version__ == expected
'@ | & $taskVenvPython -I - $taskVersion
if ($LASTEXITCODE -ne 0) { throw 'A versao instalada nao corresponde ao pacote recebido.' }

$taskCli = Join-Path $taskEnvironment 'Scripts/mcp-sentry.exe'
# Keep the help available after the downloaded ZIP/extracted folder is removed.
$taskHelp = Join-Path ([IO.Path]::GetDirectoryName($taskEnvironment)) 'ajuda-mcp-sentry'
New-Item -ItemType Directory -Path $taskHelp -Force | Out-Null
foreach ($taskGuide in @(Get-ChildItem -LiteralPath (Join-Path $taskRoot 'ajuda') -File)) {
    Copy-Item -LiteralPath $taskGuide.FullName -Destination (Join-Path $taskHelp $taskGuide.Name) -Force
}
Copy-Item -LiteralPath (Join-Path $taskDataRoot 'VERSAO.json') -Destination (Join-Path $taskHelp 'VERSAO.json') -Force
Write-Output ''
Write-Output "MCP Sentry $taskVersion instalado e conferido."
Write-Output "Ambiente: $taskEnvironment"
Write-Output "Ajuda instalada: $taskHelp"
$taskCliQuoted = $taskCli.Replace("'", "''")
Write-Output "Comando: & '$taskCliQuoted' setup"
if ($taskPrevious) { Write-Output "Instalacao anterior: $taskPrevious. Manifestos, referencias e autorizacoes nao foram alterados. Reinicie as conexoes que usam este ambiente." }
else { Write-Output 'O programa esta instalado; um MCP ainda precisa ser conectado pelo setup.' }
Write-Output 'O setup oferece selecao do MCP, confirmacoes separadas e backup da configuracao.'

$taskRunSetup = [bool]$Configurar
if (!$Configurar -and !$SemConfigurar -and !$taskPrevious) {
    Write-Output 'Deseja abrir o assistente de configuracao agora? [s/N]'
    try { $taskAnswer = Read-Host 'Resposta' }
    catch { $taskAnswer = '' }
    $taskRunSetup = $taskAnswer -match '^(s|sim)$'
}
if ($taskRunSetup) {
    if (!$Cliente) {
        if ($ClaudeConfig) { $Cliente = 'claude-desktop' }
        elseif ($CodexConfig) { $Cliente = 'codex' }
        else {
            Write-Output 'Cliente: 1 = Codex; 2 = Claude Desktop'
            $taskClientAnswer = Read-Host 'Escolha'
            if ($taskClientAnswer -eq '1') { $Cliente = 'codex' }
            elseif ($taskClientAnswer -eq '2') { $Cliente = 'claude-desktop' }
            else { throw 'Selecao invalida. O programa foi instalado; execute setup --client codex ou setup --client claude-desktop.' }
        }
    }
    $taskSetupArgs = @('setup','--client',$Cliente)
    if ($AprovarNoChat) { $taskSetupArgs += '--conversation-approval' }
    if ($CodexConfig) { $taskSetupArgs += @('--codex-config', $CodexConfig) }
    if ($ClaudeConfig) { $taskSetupArgs += @('--claude-config', $ClaudeConfig) }
    if ($StateRoot) { $taskSetupArgs += @('--state-root', $StateRoot) }
    & $taskCli @taskSetupArgs
    if ($LASTEXITCODE -ne 0) { throw 'O Sentry foi instalado, mas a configuracao nao foi concluida. Leia o diagnostico acima e execute setup novamente quando estiver pronto.' }
} else {
    Write-Output 'Configuracao nao iniciada. Execute o comando setup acima quando desejar.'
}
