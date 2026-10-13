$ErrorActionPreference='Stop'
$raizTeste='C:\MCP-Sentry-Mostratec'
Start-Transcript -Path "$raizTeste\evidencias\preparacao\reaprovar-donna-anexo-$((Get-Date).ToString('yyyyMMdd-HHmmss')).txt"
try {
    & "$raizTeste\instalacoes\sentry\Scripts\python.exe" "$raizTeste\operador\scripts\reaprovar_donna_anexo.py"
    if ($LASTEXITCODE -ne 0) { throw 'Reaprovacao falhou; preserve o transcript e nao repita automaticamente.' }
} finally { Stop-Transcript }
