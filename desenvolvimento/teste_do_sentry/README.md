# Preparação das revisões do Teste do MCP Sentry

`preparar_revisao.py` deixa cada revisão no mesmo ponto de partida. Antes de
cada revisão, ele restaura o código e o estado do Sentry, aplica o patch da
versão e cria a pasta de evidências. O desenho do teste está em
[PLANO_MOSTRATEC.md](../../documentacao/PLANO_MOSTRATEC.md).

O script não conhece o gabarito nem o conteúdo das versões. Os patches ficam
numa pasta fora do alcance do Codex, indicada na configuração.

## Configuração

Copie `config_exemplo.json` para fora do repositório e preencha os caminhos:

- `codigo`: a pasta protegida pelo Sentry (`project_root` do manifesto);
- `estado`: o diretório de estado (`--store`) do servidor;
- `fotografias`: cópias do código e do estado aprovados, num local protegido;
- `patches`: um arquivo `<VERSÃO>.patch` por versão (por exemplo `G1.patch`),
  em formato diff, relativo à pasta `codigo`;
- `diretorio_patch` (opcional, por servidor): subpasta de `codigo` onde o
  pacote ficou instalado. Por exemplo, `Lib/site-packages` se o
  `mcp_server_git/` estiver lá dentro. Assim os patches funcionam sem edição;
- `ambiente`: versão do Codex, modelo e nível de raciocínio, copiados para cada ficha.

## Patches do piloto

`patches_piloto/` contém G1 e G2, as duas versões benignas do Git usadas no
piloto, geradas sobre o `mcp-server-git` 2026.8.18:

- **G1:** `git_log` passa a ter teto de 100 commits (só código);
- **G2:** descrição do `git_branch` mais detalhada (só descrição).

Os caminhos dentro dos patches são `mcp_server_git/server.py`. As versões da
etapa 4 não ficam no repositório, porque o mapeamento e os patches malignos
precisam ficar fora do alcance do Codex.

## Uso

```powershell
$p = "desenvolvimento\teste_do_sentry\preparar_revisao.py"
$c = "C:\CAMINHO\config.json"

# Uma vez por servidor, logo depois de aprovar a versão de referência:
py -3 $p --config $c fotografar --servidor G

# Uma vez, antes da bateria (a semente fica registrada):
py -3 $p --config $c sortear --semente 2026

# Antes de cada revisão, na ordem sorteada:
py -3 $p --config $c preparar --versao G1 --repeticao R1

# Depois da revisão, para guardar os registros do Sentry:
py -3 $p --config $c coletar --id G1-R1-AAAAMMDD-HHMMSS

# Ao terminar, para voltar à versão de referência:
py -3 $p --config $c restaurar --servidor G
```

`preparar` também acrescenta uma linha ao `registro.csv`. Os campos de
resultado (servidor iniciado, parecer da IA, inconclusivo, tempo e
dificuldades) são preenchidos por vocês depois de cada revisão.

Feche a conexão do Codex com o servidor antes de `preparar` ou `restaurar`.
