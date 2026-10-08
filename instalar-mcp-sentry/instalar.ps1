param([string]$PythonExe)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskWheel = Join-Path $taskRoot 'mcp_sentry_gateway-1.0.0-py3-none-any.whl'
$taskChecksums = Get-Content -LiteralPath (Join-Path $taskRoot 'SHA256SUMS.txt')
$taskLine = @($taskChecksums | Where-Object { $_ -match '^([0-9a-fA-F]{64})\s+\*?mcp_sentry_gateway-1\.0\.0-py3-none-any\.whl$' })
if ($taskLine.Count -ne 1) { throw 'Soma do instalador ausente ou ambigua.' }
$taskExpected = ($taskLine[0] -split '\s+')[0].ToLowerInvariant()
$taskStream = [System.IO.File]::OpenRead($taskWheel)
$taskHasher = [System.Security.Cryptography.SHA256]::Create()
try { $taskActual = ([System.BitConverter]::ToString($taskHasher.ComputeHash($taskStream))).Replace('-','').ToLowerInvariant() }
finally { $taskStream.Dispose(); $taskHasher.Dispose() }
if ($taskActual -ne $taskExpected) {
    throw 'O arquivo de instalacao difere da soma recebida. Obtenha o pacote novamente.'
}
$taskVenvPython = Join-Path $taskRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $taskVenvPython)) {
    if ($PythonExe) { & $PythonExe -m venv (Join-Path $taskRoot '.venv') }
    else { & py -3 -m venv (Join-Path $taskRoot '.venv') }
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar ambiente Python.' }
}
& $taskVenvPython -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 ou posterior e necessario.' }
& $taskVenvPython -m pip install --no-index --no-deps $taskWheel
if ($LASTEXITCODE -ne 0) { throw 'Instalacao nao concluida.' }
@'
import mcp_sentry_gateway
assert mcp_sentry_gateway.__version__ == "1.0.0"
print("MCP Sentry 1.0.0 instalado.")
'@ | & $taskVenvPython -
if ($LASTEXITCODE -ne 0) { throw 'Falha ao conferir a versao instalada.' }
Write-Output 'Leia README.md e execute .\.venv\Scripts\mcp-sentry.exe setup para conectar seu MCP.'
