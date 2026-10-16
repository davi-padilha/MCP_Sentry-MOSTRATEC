# Sentry 1.3.1 / GPT-6.1 Sol low

Campanha encerrada em 16/10/2026, com 24 casos e duas repeticoes. Mesmo protocolo, politicas e gabarito v2 das campanhas anteriores.

| Indicador | Resultado |
|---|---:|
| Acertos principais | 48/48 |
| Legitimas bloqueadas | 0/26 |
| Maliciosas permitidas | 0/22 |
| Inconclusivas | 0 |
| Acertos R3 | Nenhuma R3 exigida |
| Tentativas tecnicas preservadas fora das principais | 1 |
| Backends iniciados | 0 |

## Validacao e limites

As 48 principais selecionadas passaram na auditoria de modelo/esforco, tres turnos, pedidos fixos, bloqueio inicial, escopo, referencia e envelope. Inconclusivas de registro permanecem na selecao; tentativas tecnicas sao publicadas em grupo separado e nunca apagadas. As R3 sao diagnosticas, fora das 48 principais.

A tentativa tecnica de Luna low usou PowerShell para listar a pasta ficticia em vez do MCP e foi reposta. A tentativa tecnica de Sol low nao comprovou o bloqueio inicial e foi reposta. Cada evento aparece apenas em sua respectiva serie; as outras duas nao tiveram reposicoes.

Resultados descritivos de 24 casos repetidos, nao 48 casos independentes. Nao comprovam superioridade geral nem efeito causal isolado do modelo ou da atualizacao. Mesma conta Windows, com pastas/sandbox. Previews truncadas limitam a comprovacao da entrega integral do dossie. Tempos de turno incluem modelo e ferramentas; etapas do gateway sao aninhadas. Tokens nao equivalem a cobranca.

## Arquivos

- [resumo.json](resumo.json): contagens e ambiente efetivo.
- [metricas_por_grupo.csv](metricas_por_grupo.csv): agregados com gabarito v2.
- [execucoes_publicas.csv](execucoes_publicas.csv): todas as tentativas, com uso principal/diagnostico/tecnica_excluida.
- [turnos_publicos.csv](turnos_publicos.csv): tokens e tempos por turno, sem mensagens.
- [tempos_gateway.csv](tempos_gateway.csv): medicoes por etapa, sem argumentos ou retornos.
- [tempos-e-consumo.json](tempos-e-consumo.json): agregados separados por uso.
- [proveniencia.json](proveniencia.json): hashes e regras de exportacao.

[Comparacao das quatro configuracoes](../COMPARACAO_SENTRY_131.md). [Replicacao em outra maquina](../../../reproducao-experimentos/sentry-1.3.1/README.md).
