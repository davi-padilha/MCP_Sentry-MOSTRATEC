param([Parameter(Mandatory=$true)][ValidateSet('F','G','D')][string]$Servidor,
      [string]$Raiz='C:\MCP-Sentry-Mostratec')
$ErrorActionPreference='Stop'
if ([IO.Path]::GetFullPath($Raiz) -ne 'C:\MCP-Sentry-Mostratec') { throw 'Raiz inesperada.' }
$started=Get-Date
Start-Transcript -Path "$Raiz\evidencias\preparacao\referencia-$Servidor-$($started.ToString('yyyyMMdd-HHmmss')).txt"
try {
  & "$Raiz\instalacoes\sentry\Scripts\python.exe" "$Raiz\operador\scripts\preparar_referencia_etapa4.py" $Servidor --root $Raiz
  if ($LASTEXITCODE -ne 0) { throw 'Preparacao falhou; preserve o transcript.' }
} finally { Stop-Transcript }
