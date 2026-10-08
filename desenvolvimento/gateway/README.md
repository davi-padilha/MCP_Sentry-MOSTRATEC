# Desenvolvimento do gateway atual

Código-fonte da distribuição 1.0.0 do protótipo. O usuário recebe a pasta
[instalar-mcp-sentry/](../../instalar-mcp-sentry/README.md), com o wheel e seu manual.
O protótipo antigo está em [prototipo-feicit/](../../prototipo-feicit/README.md).

A 1.0.0 distingue erros de campos ausentes e formatos misturados, com instruções
de recuperação e rejeição de vínculos inválidos. O diff contém 12 linhas de
contexto, hashes dos arquivos alterados e limites explícitos da comparação.
As orientações do dossiê entram em sua identidade; não certificam privacidade
nem escolhem automaticamente a decisão. As ferramentas nativas são preservadas.
As distribuições anteriores ficam em `pacote-usuario/` para reprodução.

A 0.10.0 acrescenta `review_binding` às evidências, erros com código e
interface de releitura, recibo do parecer efetivamente persistido e contrato
de privacidade declarado pelo operador. As medições locais por etapa ficam
fora dos hashes e não alteram as respostas nativas. A telemetria é auxiliar;
falhas nos registros obrigatórios continuam impedindo a transição de decisão.
Os campos antigos de entrada do parecer permanecem compatíveis. Copie os
quatro campos de `review_binding` para o parecer sem alterar seus valores.

A 0.11.0 oferece registro por `review_token`, emitido somente apos leitura
completa na mesma conexao e vinculado ao dossie lido. Envie `review_token`,
`decision`, `justification` e `risks`, ou use o formato anterior `verdict`.
Tokens inventados, de outra conexao, expirados ou ligados a outra atualizacao
continuam rejeitados. Os erros orientam releitura e reenvio.

A CLI `status` consulta todas as conexoes protegidas sem escrever no estado.
`restore-codex --installation-record CAMINHO` apresenta uma restauracao seletiva;
`--apply` aplica com backup e rejeicao de conflitos. O setup novo guarda
`codex-installation.json`; instalacoes antigas sem esse registro exigem
conferencia manual do backup. Estado, credenciais e pacotes nao sao removidos.

As medidas de inicializacao separam verificacao anterior ao processo, captura
da origem, copia verificada, criacao do processo, negociacao MCP e catalogo.
`startup_total` contem essas etapas; nao some novamente ao tempo do turno.
Nenhum cache de integridade foi introduzido.

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

[Validacao da 0.11.0](../../documentacao/VALIDACAO_0.11.0.md).

[Guia do piloto](../../documentacao/GUIA_PILOTO.md).
