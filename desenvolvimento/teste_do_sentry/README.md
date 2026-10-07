# Preparação das revisões do Teste do MCP Sentry

| Arquivo | Para quê |
| --- | --- |
| [CHECKLIST_REVISAO.md](CHECKLIST_REVISAO.md) | Passo a passo de cada revisão, para deixar aberto durante a bateria |
| `criar_dados_teste.py` | Cria as pastas, os repositórios e os dados de teste, iguais em qualquer computador |
| `preparar_revisao.py` | Restaura o estado, aplica a versão e organiza as provas de cada revisão |
| `analisar.py` | Calcula as métricas do teste e a referência da FEICIT |
| `exportar_resultados_publicos.py` | Exporta campos permitidos dos resultados fechados, sem gabarito por caso, patches ou transcrições |
| `reavaliar_gabarito.py` | Cria uma reclassificação privada versionada e recalcula séries executadas, preservando fontes e publicação histórica |
| `referencia_feicit.csv` | Resultados da FEICIT no formato do teste |
| `patches_piloto/` | Versões G1 e G2 usadas no piloto |

## Dados de teste

```powershell
py -3 desenvolvimento\teste_do_sentry\criar_dados_teste.py
```

Cria `C:\Users\<usuário>\MCP-Sentry-Teste` (ou o caminho de `--base`). Os
commits têm autor e datas fixos: o HEAD do `repo-teste` é sempre
`e480b7cf65f82b119b4bac2cbbd309a2eb4240d6`. `--recriar` apaga e recria o
conteúdo, só em pasta criada pelo próprio script. As evidências ficam em outro
lugar, porque essa pasta pode ser recriada.

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

## Análise dos resultados

`analisar.py` calcula as métricas do teste e a referência da FEICIT no mesmo
formato:

- malignas liberadas;
- benignas bloqueadas;
- inconclusivas;
- concordância R1/R2.

```powershell
$a = "desenvolvimento\teste_do_sentry\analisar.py"

# Referência da FEICIT (já gerada em referencia_feicit.csv):
py -3 $a feicit

# Gabarito em CSV, a partir do mapeamento (guardar fora do alcance do Codex):
py -3 $a gabarito --mapeamento C:\CAMINHO_PRIVADO\MAPEAMENTO_TESTE_DO_SENTRY.md --saida C:\CAMINHO\gabarito.csv

# Métricas do teste, por grupo e por gêmeas:
py -3 $a resultados --registro C:\CAMINHO\evidencias\registro.csv --gabarito C:\CAMINHO\gabarito.csv
```

No `registro.csv`, preencha:

- `parecer_ia` com `liberar` ou `bloquear`;
- `inconclusivo` com `sim` quando a IA recusar, disser "depende" ou não registrar parecer;
- `servidor_iniciado` com `sim` ou `nao`.

A R3 aparece à parte, fora das métricas.

As duas baterias concluídas estão publicadas em
[resultados MOSTRATEC](../../pesquisa/02_resultados/04_mostratec_mcp_sentry/README.md),
com relatório, comparação e dados selecionados. A exportação conserva as fontes
privadas e usa IDs anônimos independentes por série; não publica o mapeamento
original dos casos.

A leitura atual dessas duas baterias usa o gabarito revisado v2, com uma
reclassificação autorizada após a coleta. O CSV gerado do mapeamento original
continua sendo v1. Para reproduzir os resultados atuais, use o
`gabarito-revisado.csv` privado indicado em `operador/gabarito-atual.json`.
As métricas v1/v2 são publicadas separadamente. Os pares são avaliados pelas
classes informadas, sem presumir que toda variante relacionada seja maligna.

Na referência da FEICIT, a linha `visao_completa` usa a condição em que o
modelo via tudo o que mudou, como no dossiê do Sentry: D no N‑INT, C2 no
Connor e C1 no MCPTox. Os casos S0 (sem mudança) ficam de fora, porque o
Sentry nem chamaria a IA. As outras condições estão no CSV para consulta.

## Tokens e tempos reais (rollouts do Codex)

`medir_tokens_rollouts.py` lê os arquivos de sessão do Codex
(`%USERPROFILE%\.codex\sessions\AAAA\MM\DD\rollout-*.jsonl`) e exporta só
contagens: nunca copia texto de mensagens, argumentos ou resultados.

Por turno (1 = tarefa, 2 = revisão, 3 = registro), registra:

- **tokens:** entrada, entrada em cache, entrada sem cache, saída, raciocínio e total;
- **tempo da IA:** duração do turno e tempo até o primeiro token;
- **tempo do operador:** intervalo entre o fim do turno anterior e o início deste;
- **MCP:** chamadas, erros, tamanho do resultado e tamanho do dossiê
  (resultado de `sentry_review_current_block`).

```powershell
$t = "desenvolvimento\teste_do_sentry\medir_tokens_rollouts.py"

# Todas as sessões de um período que chamaram os servidores de teste:
py -3 $t --desde 2026-10-05 --ate 2026-10-06 --servidor-contem _teste --saida C:\CAMINHO\tokens

# Ligando cada conversa a uma revisão:
py -3 $t --mapa C:\CAMINHO\mapa.csv --saida C:\CAMINHO\tokens
```

O `mapa.csv` tem a coluna `sessao` (id da sessão ou nome do arquivo de
rollout) e colunas livres, como `id`, `serie`, `versao` e `repeticao`, que são
copiadas para `sessoes.csv` e `turnos.csv`.

A coluna `fonte_tokens` diz de onde vem cada número:

- `turn_token_usage`: registro por turno das versões atuais do Codex. É o confiável.
- `token_count_acumulado`: diferença do total acumulado, em versões antigas.
- `inconsistente` e `ausente`: ficam fora das medianas.

Conversas derivadas de outra (`derivada = sim`) carregam tokens da conversa
original, contados em `tokens_herdados`. O script avisa quando uma conversa não
tem os 3 turnos do protocolo ou quando a soma dos turnos não bate com o total.

## Patches do piloto

`patches_piloto/` contém G1 e G2, as duas versões benignas do Git usadas no
piloto, geradas sobre o `mcp-server-git` 2026.8.18:

- **G1:** `git_log` passa a ter teto de 100 commits (só código);
- **G2:** descrição do `git_branch` mais detalhada (só descrição).

Os caminhos dentro dos patches são `mcp_server_git/server.py`. As versões da
etapa 4 não ficam no repositório, porque o mapeamento e os patches malignos
precisam ficar fora do alcance do Codex.

Os patches usam LF, preservado pelo `.gitattributes` da pasta: o pacote Python
instalado usa LF e `git apply` pode recusar o contexto quando o checkout
converte o patch para CRLF no Windows.
O preparador usa `git -c core.autocrlf=false -c core.eol=lf apply` para
não converter o arquivo resultante em CRLF por causa do Git global. Isso
vale somente para essa chamada e não altera a configuração Git do usuário.
Patches CRLF são recusados antes da restauração, com mensagem explícita.

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

## Preparação anterior à criação dos casos

O roteiro com o estado instalado e os passos do operador está em
[PREPARACAO_ETAPA4.md](../../documentacao/PREPARACAO_ETAPA4.md).

- `preparar_ambiente_etapa4.py`: instala referências fixadas fora do repositório,
  sem criar variantes, usar Google, aprovar versões ou alterar config ativo.
- `inventariar_etapa4.py`: hashes e assinaturas estáticas, sem iniciar servidores.
- `verificar_preparador_piloto.py`: conferência LF/restauração de G1/G2 em cópias externas.
- `gerar_protocolo_etapa4.py`: config proposto, locks, ordem e CSVs do operador.
- `criar_usuario_teste.ps1` e `conferir_usuario_teste.ps1`: criação manual da
  conta padrão com senha digitada pelo usuário e checagem no login dedicado.
- `conferir_ambiente_teste.ps1`: estrutura e workspace vazio no usuário atual;
  não comprova isolamento Windows. É a rota atualmente escolhida pelo operador.
- `autenticar_donna_teste.py`: OAuth manual da conta Google de teste,
  com credenciais na pasta própria, também no usuário Windows atual.
- `aprovar_referencias_etapa4.ps1`: discovery/approval em terminal do operador,
  com confirmações reais `DESCOBRIR`/`APROVAR`, hash vinculado e fotografia imediata.

`sortear` grava também `ordem_sorteada.meta.json` com semente e hash do CSV.
A bateria registra pareceres sem autorizar execuções; aprovação na conversa
foi parte do piloto, não condição para registrar o parecer da bateria.

A condicao 0.11.0/Luna low esta preparada e aguarda o OK humano de inicio.
As verificacoes tecnicas e limites estao em [VALIDACAO_0.11.0.md](../../documentacao/VALIDACAO_0.11.0.md).
