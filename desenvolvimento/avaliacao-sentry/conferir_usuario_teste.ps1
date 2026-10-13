param([string]$Raiz='C:\MCP-Sentry-Mostratec')
$ErrorActionPreference='Stop'
if ($env:USERNAME -ne 'SentryMostratec') { throw 'Execute no usuario Windows dedicado SentryMostratec.' }
if ([IO.Path]::GetFullPath($Raiz) -ne 'C:\MCP-Sentry-Mostratec') { throw 'Raiz inesperada.' }
$privatePaths=@("$Raiz\operador",'C:\Users\davig\OneDrive\Documentos\GitHub\MCP-Sentry-FEICIT')
foreach ($privatePath in $privatePaths) {
  try { [void][IO.Directory]::GetFileSystemEntries($privatePath); throw "Pasta privada legivel: $privatePath" }
  catch [UnauthorizedAccessException] { Write-Host "Acesso recusado conforme esperado: $privatePath" }
}
foreach ($folder in @('instalacoes','config','codigo')) {
  $probe="$Raiz\$folder\teste-escrita-usuario.txt"
  try { [IO.File]::WriteAllText($probe,'probe'); throw "Escrita indevida permitida: $folder" }
  catch [UnauthorizedAccessException] { Write-Host "Escrita recusada conforme esperado: $folder" }
}
$workspace="$Raiz\workspace-codex"
[IO.File]::WriteAllText("$workspace\probe.txt",'workspace gravavel')
Remove-Item -LiteralPath "$workspace\probe.txt"
if (-not (Test-Path -LiteralPath "$env:USERPROFILE\.ssh\id_ed25519")) {
  [void](New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force)
  Write-Host 'Crie sua chave SSH de teste com ssh-keygen; nao reutilize a chave pessoal.'
}
& "$Raiz\runtimes\python\python.exe" --version
if ($LASTEXITCODE -ne 0) { throw 'Runtime Python nao acessivel ao usuario dedicado.' }
Write-Host 'Checagem de acesso concluida. Abra o Codex apenas em workspace-codex; nao importe projetos, memorias ou skills pessoais.'
