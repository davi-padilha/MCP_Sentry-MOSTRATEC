# MCP Sentry 1.0.0 — Luna Low

Coleta nova autorizada por **“OK para iniciar”**, iniciada e encerrada em
07/10/2026, horário de Brasília. A tentativa cancelada anterior
foi preservada separadamente e nenhuma de suas revisões foi reutilizada.

Foram concluídas 48 conversas principais, com os títulos exatos
**Teste v1 Luna Low 1** até **Teste v1 Luna Low 48**. Quatro conversas
**Teste v1 Luna Low R3 1** a **Teste v1 Luna Low R3 4** são diagnósticas e
ficam fora do denominador principal. Os 52 títulos e o arquivamento foram
conferidos na listagem do aplicativo ao final.

## Resultados principais

Mesmos 24 casos, duas repetições, ordem e pedidos congelados, política
`mcp-sentry-review-v2` e gabarito revisado v2; 13 versões benignas e 11 malignas.

| Resultado | Quantidade |
|---|---:|
| Conversas principais | 48 |
| Malignas bloqueadas | 22 de 22 |
| Malignas liberadas | 0 de 22 |
| Benignas liberadas | 14 de 26 |
| Benignas bloqueadas | 11 de 26 |
| Inconclusivas | 1 de 48, em caso benigno |
| Pareceres principais persistidos, com recibo conferido | 47 |
| Pares R1/R2 concordantes | 20 de 24 |
| R3 diagnósticas | 4, todas com parecer liberar |

**Esses são resultados observados, não uma coleta aprovada pela auditoria
estrita.** Duas conversas não comprovaram o bloqueio inicial por chamada MCP:
uma posteriormente revisou e registrou o parecer, e a outra ficou inconclusiva
por indisponibilidade das ferramentas. Esta última fez chamadas de shell fora
do roteiro e não registrou parecer MCP. Duas outras conversas fizeram consultas
de catálogo fora do roteiro. Portanto, há 46 bloqueios iniciais comprovados
e três conversas principais com chamadas fora do roteiro.

O consolidador estrito recusou a coleta no requisito de bloqueio inicial.
Seus requisitos não foram relaxados. Não foram exportadas linhas anônimas
de execuções por esse consolidador. A inconclusiva e os desvios foram
preservados, sem substituir tentativas para melhorar os resultados.

## Conferências e restauração

- Modelo `gpt-6-luna` e esforço `low` confirmados nos 156 turnos das 52 conversas.
- Memória desligada; conversas novas e sem herança de outra conversa.
- Todos os três pedidos por conversa foram conferidos.
- 51 pareceres persistidos ao todo, com recibos conferidos; nenhum autoriza execução.
- Nenhum início de backend alterado observado nos registros.
- Aprovações e envelopes permaneceram inalterados durante as revisões.
- Evidências coletadas e conversa arquivada antes da preparação seguinte.
- Git, Filesystem e Donna restaurados às referências: `doctor: ready`, sem issues.

Os casos com ausência de chamada inicial não devem ser descritos como bloqueio
técnico comprovado. Os números não demonstram classificação infalível nem
isolam o efeito da versão do gateway. Os limites históricos do desenho e dos
casos permanecem aplicáveis.

## Consumo medido

Contagens `turn_token_usage` dos rollouts efetivos; entrada em cache é parte
da entrada, não deve ser somada novamente. Tokens de raciocínio integram a saída.

| Tokens | Principais | R3 |
|---|---:|---:|
| Entrada | 15.485.292 | 1.181.839 |
| Entrada em cache | 13.859.840 | 1.054.208 |
| Saída | 43.781 | 3.418 |
| Raciocínio | 2.651 | 102 |
| Total | 15.529.073 | 1.185.257 |

As fontes completas, transcrições, gabarito, mapas de conversas e fechamento
com limites permanecem na área privada da série nova. O registro histórico
e a tentativa cancelada continuam preservados. Nenhuma variante foi aprovada
para execução e nenhuma publicação externa foi realizada.
