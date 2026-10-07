# Validacao do gateway 0.11.0

As cinco evolucoes de usabilidade foram implementadas. Esta etapa apenas
valida e prepara o prototipo; a nova bateria aguarda o OK do usuario.

## Mudancas

1. Erros recuperaveis indicam o motivo, a ferramenta de releitura e como
   reenviar o parecer. Identificadores e hashes incorretos continuam rejeitados.
2. `mcp-sentry status` consulta todas as conexoes locais protegidas, agrupando
   execucao e revisao. Mostra hash e data da referencia aprovada, mudanca
   pendente, ultimo parecer, aplicabilidade desse parecer e espera de decisao
   humana. Nao escreve no estado nem inicia o backend. A versao exibida do
   comando nao e apresentada como versao de gateways instalados por outro runtime.
3. `mcp-sentry restore-codex --installation-record CAMINHO` apresenta a
   restauracao das entradas alteradas pelo setup; `--apply` aplica com backup.
   Preserva opcoes e servidores alheios. Conflitos de valores ou comentarios
   nas entradas geridas interrompem a operacao. Normalizacao de LF/CRLF e
   separadores vazios nao e tratada como alteracao de conteudo. O setup novo
   grava `codex-installation.json`; instalacoes antigas sem esse registro
   exigem conferencia manual do backup. Pacotes e estado nao sao removidos.
4. A inicializacao mede verificacao anterior ao processo, captura da origem,
   copia verificada, criacao do processo, negociacao MCP, conferencia de
   catalogo e total. O coletor separa duracao registrada dos turnos e intervalos
   entre eles. Os intervalos incluem orquestracao e espera do operador;
   duracao do turno inclui modelo, ferramentas e esperas internas. Diferencas
   de resolucao dos timestamps ficam explicitas. Tempos do gateway estao
   contidos nos turnos; nao devem ser somados novamente. Nao medimos latencia
   pura do modelo nem introduzimos cache da copia verificada.
5. O registro aceita `review_token`, `decision`, `justification` e `risks`.
   O token aleatorio e emitido somente apos leitura completa na mesma conexao
   e guarda os vinculos daquele dossie. Tokens inventados, de outra conexao,
   expirados ou ligados a uma atualizacao anterior sao rejeitados. O formato
   antigo `verdict` permanece aceito; os dois formatos nao podem ser misturados.
   O token nao autentica o usuario nem autoriza execucao. O recibo devolve
   os identificadores efetivamente persistidos e o texto mascarado.

As instrucoes da interface de execucao orientam tentar a ferramenta nativa
solicitada primeiro e parar se bloqueada. Nao alteram as descricoes ou schemas
das ferramentas nativas nem garantem o comportamento do modelo.

## Evidencias tecnicas

- Suite completa: 107 testes, resultado OK, um ignorado por limitacao de
  symlink da plataforma. A fonte final do comando administrativo tambem passou
  nos 11 testes de usabilidade. Apuracao de tempos: dois testes passaram.
- Uma execucao na pasta sincronizada do OneDrive teve `WinError 5` na escrita
  atomica de uma fixture. A suite completa passou em copia de fonte e testes
  fora do OneDrive. Nenhuma validacao de producao foi enfraquecida para ocultar
  essa falha. Os testes tambem encontraram a necessidade de normalizar LF/CRLF
  na restauracao e uma fixture que precisava editar o cabecalho TOML entre
  aspas efetivamente gerado. Ambos foram ajustados antes da conclusao.
- SDK MCP real: seis interfaces, registro por token e por formato antigo,
  schemas de resposta, erro de identificador e recibos de liberar/bloquear
  conferidos contra a persistencia; a referencia aprovada permaneceu intacta.
- Leituras nativas `git_log`, `list_directory` e `consultar_agenda` passaram.
  Os estados usados nos controles foram restaurados; essas chamadas nao sao
  revisoes da bateria.
- Python, JavaScript e PowerShell da instrumentacao passaram na verificacao
  de sintaxe, sem executar o orquestrador.
- O comando instalado `status` agrupou as seis conexoes ficticias em tres
  servidores, retornou `unchanged` e deixou todos os arquivos de estado
  identicos. Configuracao ativa preservada e congelamento conferido.

No controle final, a inicializacao do Filesystem levou aproximadamente
44,70 s, com 39,84 s de copia e verificacao. Git levou 1,18 s e Donna 2,31 s.
Sao observacoes tecnicas individuais, nao medias nem garantias de desempenho;
o tempo da consulta externa nao esta incluido no total de inicializacao.

## Pacote e congelamento

Wheel: `pacote-usuario/mcp_sentry_gateway-0.11.0-py3-none-any.whl`.
SHA-256: `a3e16dcdca8b71ebe5569be9da5d924ef486325727269d006338c96acb58c8ba`.
Os 16 modulos instalados conferem com o wheel e a fonte.

A condicao preparada usa GPT-6 Luna/low, politicas preservadas, gabarito
revisado v2, mesmos 24 patches, duas repeticoes, mesma ordem e mesmos pedidos.
Memoria desativada. As conversas novas serao criadas somente durante a bateria,
com modelo/esforco explicitos e conferencia dos contextos efetivos no rollout.
Ainda nao ha revisoes de modelo desta condicao 0.11.0.

A serie nova tem registro vazio, referencias restauradas e `doctor: ready`
para os tres servidores. A configuracao ativa do aplicativo foi preservada;
a proposta da nova serie so sera ativada depois do OK. Nenhuma autorizacao
de inicio esta ativa. A revisao preliminar anterior da 0.10.0 e todas as
series historicas continuam separadas e preservadas. Sem commit ou push.
