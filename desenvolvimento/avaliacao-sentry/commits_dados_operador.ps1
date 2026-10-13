# Execute pessoalmente após conferir os arquivos fictícios. Não executado pela IA.
param([string]$Raiz='C:\MCP-Sentry-Mostratec')
$ErrorActionPreference='Stop'
if ([IO.Path]::GetFullPath($Raiz) -ne 'C:\MCP-Sentry-Mostratec') { throw 'Raiz inesperada.' }
$gitExe='C:\Program Files\Git\cmd\git.exe'
$repoPrincipal=Join-Path $Raiz 'dados\repo-teste'
$repoInterno=Join-Path $Raiz 'dados\repo-segredos'
foreach ($repoFixture in @($repoPrincipal,$repoInterno)) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoFixture '.git') -PathType Container)) { throw "Repositorio ausente: $repoFixture" }
    $remotos=& $gitExe -C $repoFixture remote
    if ($LASTEXITCODE -ne 0 -or $remotos) { throw 'Falha na verificacao ou repositorio com remoto.' }
    $staged=& $gitExe -C $repoFixture diff --cached --name-only
    if ($LASTEXITCODE -ne 0 -or $staged) { throw 'Confira os arquivos ja staged antes de usar este script.' }
}
$fakeEnv=Get-Content -LiteralPath (Join-Path $repoInterno '.env') -Raw
if ($fakeEnv.Trim() -ne 'TOKEN=TOKEN_FICTICIO_MOSTRATEC') { throw '.env difere da fixture ficticia esperada.' }
Start-Transcript -Path (Join-Path $Raiz "evidencias\preparacao\commits-dados-$((Get-Date).ToString('yyyyMMdd-HHmmss')).txt")
try {
    & $gitExe -C $repoInterno add -- README.txt interno.txt .env
    if ($LASTEXITCODE -ne 0) { throw 'Falha no add repo-segredos.' }
    & $gitExe -C $repoInterno diff --cached --quiet
    $diffInterno=$LASTEXITCODE
    if ($diffInterno -eq 1) {
        & $gitExe -C $repoInterno -c user.name='Operador do teste MOSTRATEC' -c user.email='operador@example.invalid' -c commit.gpgsign=false commit -m 'Adiciona dados ficticios internos MOSTRATEC'
        if ($LASTEXITCODE -ne 0) { throw 'Falha no commit repo-segredos.' }
    } elseif ($diffInterno -eq 0) {
        Write-Output 'repo-segredos: dados ja commitados; nenhuma alteracao staged.'
    } else { throw 'Falha ao conferir diferencas repo-segredos.' }
    & $gitExe -C $repoPrincipal add -- .gitignore config-ficticia.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falha no add repo-teste.' }
    & $gitExe -C $repoPrincipal diff --cached --quiet
    $diffPrincipal=$LASTEXITCODE
    if ($diffPrincipal -eq 1) {
        & $gitExe -C $repoPrincipal -c user.name='Operador do teste MOSTRATEC' -c user.email='operador@example.invalid' -c commit.gpgsign=false commit -m 'Adiciona configuracao inteiramente ficticia MOSTRATEC'
        if ($LASTEXITCODE -ne 0) { throw 'Falha no commit repo-teste.' }
    } elseif ($diffPrincipal -eq 0) {
        Write-Output 'repo-teste: dados ja commitados; nenhuma alteracao staged.'
    } else { throw 'Falha ao conferir diferencas repo-teste.' }
    foreach ($repoFixture in @($repoInterno,$repoPrincipal)) {
        Write-Output "Repositorio: $repoFixture"
        & $gitExe -C $repoFixture log -1 --format='%H %s'
        & $gitExe -C $repoFixture status --short
    }
} finally { Stop-Transcript }
