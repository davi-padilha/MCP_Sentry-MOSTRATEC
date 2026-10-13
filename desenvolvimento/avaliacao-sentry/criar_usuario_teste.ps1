#Requires -RunAsAdministrator
param([string]$Nome='SentryMostratec', [string]$Raiz='C:\MCP-Sentry-Mostratec',
      [string]$Repositorio='C:\Users\davig\OneDrive\Documentos\GitHub\MCP-Sentry-FEICIT')
$ErrorActionPreference='Stop'
$rootPath=[IO.Path]::GetFullPath($Raiz)
if ($rootPath -ne 'C:\MCP-Sentry-Mostratec' -or -not (Test-Path -LiteralPath "$rootPath\ambiente-etapa4.json")) { throw 'Raiz de teste inesperada.' }
if ($Nome -ne 'SentryMostratec') { throw 'Nome diferente do protocolo; revise antes.' }
$operatorSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
if (Get-LocalUser -Name $Nome -ErrorAction SilentlyContinue) { throw 'Usuario ja existe; nao altero sua senha ou permissoes automaticamente.' }
$password=Read-Host 'Defina a senha do usuario Windows de teste (nao envie no chat)' -AsSecureString
$newUser=New-LocalUser -Name $Nome -Password $password -Description 'Revisoes MOSTRATEC, recursos ficticios'
$usersGroup=Get-LocalGroup -SID 'S-1-5-32-545'
Add-LocalGroupMember -Group $usersGroup -Member $newUser
$testSid=$newUser.SID.Value
# Only the standard account is created: never add it to Administrators.
& icacls.exe $rootPath /inheritance:r /grant:r "*${operatorSid}:(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' "*${testSid}:(OI)(CI)RX"
if ($LASTEXITCODE -ne 0) { throw 'ACL da raiz falhou; nao use a conta ate corrigir.' }
foreach ($folder in @('dados','estado','workspace-codex','credenciais')) {
  & icacls.exe "$rootPath\$folder" /grant:r "*${testSid}:(OI)(CI)M"
  if ($LASTEXITCODE -ne 0) { throw "ACL falhou: $folder" }
}
& icacls.exe "$rootPath\operador" /deny "*${testSid}:(OI)(CI)F"
if ($LASTEXITCODE -ne 0) { throw 'Isolamento do operador falhou.' }
if (Test-Path -LiteralPath $Repositorio) {
  & icacls.exe ([IO.Path]::GetFullPath($Repositorio)) /deny "*${testSid}:(OI)(CI)F"
  if ($LASTEXITCODE -ne 0) { throw 'Isolamento do repositorio falhou.' }
}
$record=@{usuario=$Nome;sid=$testSid;operador_sid=$operatorSid;criado_em=(Get-Date).ToString('o');administrador=$false;validacao_no_login_pendente=$true}
$record | ConvertTo-Json | Set-Content -LiteralPath "$rootPath\evidencias\preparacao\usuario-windows.json" -Encoding UTF8
Write-Host 'Usuario criado. Entre nele e execute conferir_usuario_teste.ps1 antes de abrir o Codex.'
