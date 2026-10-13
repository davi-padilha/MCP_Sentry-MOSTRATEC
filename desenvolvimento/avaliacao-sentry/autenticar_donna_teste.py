"""User-run OAuth for the test Google account; never prints credentials/tokens."""
import getpass
import sys
from pathlib import Path


def main():
    root = Path(r"C:\MCP-Sentry-Mostratec")
    credentials = root / "credenciais/donna/credentials.json"
    token = root / "credenciais/donna/token.json"
    if not credentials.is_file():
        raise RuntimeError("Coloque o cliente OAuth de teste no caminho indicado no protocolo")
    if token.exists():
        raise RuntimeError("Token já existe; confira sua conta antes de substituir")
    sys.path.insert(0, str(root / "codigo/donna"))
    from donna_mcp.providers.google import load_google_credentials
    print(f"Usuário Windows: {getpass.getuser()}. Credenciais ficam somente na pasta de teste.")
    print("Na janela Google, selecione somente a conta de teste. A autorização é feita por você.")
    load_google_credentials(credentials, token, allow_interactive=True)
    print("Token de teste salvo localmente, sem copiar para o repositório.")


if __name__ == "__main__":
    main()
