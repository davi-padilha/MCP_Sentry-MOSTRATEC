param([string]$Raiz='C:\MCP-Sentry-Mostratec')
$ErrorActionPreference='Stop'
$rootPath=[IO.Path]::GetFullPath($Raiz)
if ($rootPath -ne 'C:\MCP-Sentry-Mostratec') { throw 'Raiz inesperada.' }
$folders=@('workspace-codex','estado','config','instalacoes','codigo','operador','credenciais','dados')
foreach ($folder in $folders) {
  if (-not (Test-Path -LiteralPath "$rootPath\$folder" -PathType Container)) { throw "Pasta ausente: $folder" }
}
$workspace=[IO.Path]::GetFullPath("$rootPath\workspace-codex")
foreach ($folder in @('estado','config','instalacoes','codigo','operador','credenciais')) {
  $outside=[IO.Path]::GetFullPath("$rootPath\$folder")
  if ($outside.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw "Pasta de controle dentro do workspace: $folder" }
}
$contents=@(Get-ChildItem -LiteralPath $workspace -Force)
if ($contents.Count) { throw 'Workspace nao esta vazio. Preserve os arquivos e confira antes da bateria.' }
& "$rootPath\instalacoes\sentry\Scripts\python.exe" --version
if ($LASTEXITCODE -ne 0) { throw 'Runtime Python falhou.' }
Write-Host "Pastas conferidas para o usuario atual: $env:USERNAME"
Write-Host 'Nao ha isolamento entre usuarios Windows. Estado e operador devem ficar fora das raizes gravaveis do agente.'
Write-Host 'A configuracao efetiva e o sandbox precisam ser conferidos na conversa de teste antes da bateria.'
