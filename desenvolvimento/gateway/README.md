# Desenvolvimento do gateway atual

Código-fonte da candidata 0.9.1. O usuário recebe a pasta
[pacote-usuario/](../../pacote-usuario/README.md), com o wheel e seu manual.
O protótipo antigo está em [prototipo-feicit/](../../prototipo-feicit/README.md).

Na 0.9.0, o mascaramento distingue chaves secretas de literais como
`"password="`, preserva linhas físicas e evita deformar o diff. A política
opcional de privacidade fornece critérios confiados pelo operador para a
revisão. Ela não filtra respostas em execução. Configuração, promoção e
limites estão em [PRIVACIDADE.md](PRIVACIDADE.md).

A 0.9.1 sincroniza o esquema de registro do parecer com o protocolo v2,
eliminando a incompatibilidade de versão anunciada na 0.9.0. Evidências em
[VALIDACAO_0.9.1.md](../../documentacao/VALIDACAO_0.9.1.md).

Na raiz do repositório, em PowerShell:

```powershell
python -m venv .\desenvolvimento\gateway\.venv
& .\desenvolvimento\gateway\.venv\Scripts\python.exe -m pip install .\desenvolvimento\gateway
& .\desenvolvimento\gateway\.venv\Scripts\python.exe -m unittest discover -s desenvolvimento/gateway/testes -q
```

Para gerar uma distribuição nova, instale a ferramenta de build no ambiente de
desenvolvimento e execute `python -m build --wheel --outdir ../../pacote-usuario`
nesta pasta. Ambientes virtuais, testes e arquivos intermediários não fazem
parte da entrega ao usuário.

[Guia do piloto](../../documentacao/GUIA_PILOTO.md).
