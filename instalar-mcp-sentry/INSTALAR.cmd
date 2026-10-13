@echo off
setlocal DisableDelayedExpansion
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0arquivos-instalacao\instalar.ps1" %*
set "MCP_SENTRY_INSTALL_EXIT=%errorlevel%"
echo.
if not "%MCP_SENTRY_INSTALL_EXIT%"=="0" echo A instalacao nao foi concluida. Leia a mensagem acima e ajuda\SOLUCAO-DE-PROBLEMAS.md.
if /i not "%MCP_SENTRY_NO_PAUSE%"=="1" pause
exit /b %MCP_SENTRY_INSTALL_EXIT%
