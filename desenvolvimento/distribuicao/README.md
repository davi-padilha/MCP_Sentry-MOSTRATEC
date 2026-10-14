# Preparar uma distribuição do MCP Sentry

O comando abaixo monta a entrega em uma pasta isolada, valida instalação e
atualização, e somente então atualiza `instalar-mcp-sentry/` e gera o ZIP em
`distribuicoes/`. Não consulta nem modifica a configuração ativa dos clientes.

No Windows, use Python 3.11+ com `setuptools>=68` e `wheel`. Essas são
dependências de desenvolvimento; o gateway continua sem dependências de
execução adicionais. Na raiz do repositório:

```powershell
python -B desenvolvimento/distribuicao/preparar_distribuicao.py
```

Se `python` for um alias inválido, substitua pelo caminho absoluto de um
Python utilizável. Para também conferir o transporte e os schemas com o SDK
oficial, informe um Python que tenha `mcp` e `jsonschema` instalados:

```powershell
python -B desenvolvimento/distribuicao/preparar_distribuicao.py --python-sdk 'C:\CAMINHO\python.exe'
```

O script usa a versão de `desenvolvimento/gateway/pyproject.toml` e exige que
ela corresponda a `mcp_sentry_gateway.__version__`. O instalador lê a versão
gerada em `arquivos-instalacao/VERSAO.json`. Não edite o instalador a cada troca de versão.

`README_USUARIO.md.in` é a fonte do README entregue; versão, requisito Python
e nome do wheel são preenchidos automaticamente. Os demais guias e
`INSTALAR.cmd`, guias em `ajuda/` e `arquivos-instalacao/instalar.ps1` ficam
em `instalar-mcp-sentry/` e são copiados para a entrega.
Edite esses arquivos-fonte quando o comportamento mudar. Não edite os hashes
ou a identificação gerada para ocultar uma falha de validação.

## O que o comando confere

- Concordância da versão e presença de todos os módulos no wheel.
- Bytes iguais entre código-fonte, wheel e instalação.
- Suíte do gateway em uma cópia isolada.
- Instalação limpa pelo PowerShell 5.1, inclusive caminho com espaços.
- Lançador CMD e propagação de falhas; instalação em perfil descartável,
  cópia dos guias e funcionamento após retirar a pasta extraída.
- Reutilização da `.venv` antiga na raiz do pacote, mantendo seu caminho.
- Atualização da distribuição anterior 1.0.0, sem alterar sua referência e
  configuração fictícias. A 1.0.0 preservada é a origem dessa verificação.
- Descoberta automática de Python e diagnóstico de executável inválido.
- Rejeição de arquivos alterados antes de criar ambiente.
- Oferta opcional do setup, recusa respeitada e configuração com confirmações
  e backup usando um MCP fictício em Codex e Claude Desktop; diagnóstico,
  inventário e restauração do JSON do Claude em perfil descartável.
- Opção `-AprovarNoChat` nas duas interfaces do Claude e, com SDK, aceitação
  permanente seguida de chamadas repetidas, reconexão e bloqueio de nova mudança.
- Transporte `stdio`, resposta nativa, bloqueio antes do início, revisão
  separada, registro de parecer sem liberação e autorização de um início.

O ZIP contém onze arquivos: README e lançador na raiz, cinco guias em `ajuda/`
e quatro arquivos técnicos em `arquivos-instalacao/`. `.venv`, estados, logs e
credenciais não entram. Timestamps e ordem dos arquivos são fixados para que
os mesmos bytes de entrada produzam os mesmos arquivos compactados.
Wheels anteriores são preservados em `distribuicoes-historicas/`.

As evidências ficam em `laboratorio/execucoes/distribuicao-<versao>-*/` e são
ignoradas pelo Git. `arquivos-instalacao/VERSAO.json` contém somente identificação,
requisito Python, escopo, wheel/hash e data. Resultados detalhados ficam em
`validacao/validacao.json`; o registro da entrega
está em `documentacao/validacoes/VALIDACAO_1.3.1.md`. As baterias de IA têm seus próprios
resultados e hashes; construir um wheel novo não repete nem substitui essas
campanhas.

Uma falha conserva a pasta de evidências e impede a publicação da candidata.
As validações rodam em processos novos; não há retomada que presuma resultados
de uma execução anterior. Instalações locais existentes na pasta de entrega
não são apagadas pelo empacotamento.
