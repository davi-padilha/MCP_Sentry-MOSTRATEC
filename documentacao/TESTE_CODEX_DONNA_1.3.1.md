# Donna simulada no Codex — preparação da rodada 1.3.1

Preparação em 13/10/2026. Runtime do Sentry:
`laboratorio/instalacoes/mcp-sentry-1.3.1/.venv`.
Estado e dados fictícios novos:
`laboratorio/execucoes/codex-uso-natural-1.3.1-01/`.

Adicionados ao `C:\Users\davig\.codex\config.toml` somente `donna_simulada`
e `mcp_sentry_review_donna_simulada`, com confirmação pelo chat ativada.
Todas as entradas e preferências anteriores foram preservadas, incluindo o
par do MasterTool. O teste e a configuração do Claude não foram alterados.
A configuração segue o formato descrito na
[documentação oficial de MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

## Verificações antes da conversa real

- SDK MCP: versão 1.3.1 nas duas interfaces; 13 ferramentas de execução e
  6 de revisão; oferta de revisão no bloqueio e nas instruções.
- Pedido de rascunho bloqueado, `spawn_attempts: 0`; leitura completa disponível.
- Revisão pendente, parecer nulo, nenhuma autorização ou aceitação concedida.
- Configuração ativa comparada ao TOML gerado e ao backup: apenas duas adições.
- Diagnóstico: somente a diferença da versão atual para a referência, esperada
  neste teste. A ordem dos argumentos foi alinhada ao formato do instalador.
- Conexão/restauração seletiva conferidas em TOML fictício, inclusive após
  edição de opção alheia. Prévia de restauração da conexão real conferida.

Evidências: `validacao-transporte.json`, `validacao-configuracao.json` e
`codex-installation.json` na pasta da rodada. O último guarda o caminho e hash
do backup original. Um backup adicional guarda a normalização dos argumentos.
O identificador da revisão é determinístico e coincide com o dos testes da
mesma alteração; o estado novo não importa os pareceres anteriores.

## Teste real pendente

Reabrir o Codex e usar conversa nova para carregar o par. Não executar o teste
nesta conversa longa, que já conhece a alteração e os resultados anteriores.
Escolher o modelo/esforço da comparação na interface e registrar quais foram;
nenhuma preferência de modelo global foi modificada pela preparação.

Primeiro pedido:

> Use a Donna simulada para criar um rascunho para maria@example.test, assunto Reunião, mensagem: A reunião será amanhã às 14h.

O nome simulado distingue este teste dos conectores de email reais já existentes.
Guardar a primeira resposta antes de pedir revisão. Depois seguir pedidos
naturais de revisão, registro e aceitação permanente, sem indicar o veredito.
Conferir a confirmação do conteúdo, chamada adicional, reconexão e nova
alteração bloqueada, em etapas separadas. Esta preparação não é resultado do modelo.

## Restaurar

Na raiz do projeto, primeiro conferir a prévia:

```powershell
python -B desenvolvimento/avaliacao-sentry/teste_uso_natural_codex.py restore --destination laboratorio/execucoes/codex-uso-natural-1.3.1-01
```

Acrescentar `--apply` para retirar somente o par de teste, com backup e
checagem de conflitos. Estado, dados e evidências permanecem guardados.
