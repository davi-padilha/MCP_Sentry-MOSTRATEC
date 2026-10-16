# Campanhas MCP Sentry 1.3.1 — Luna e Sol

Publicação das campanhas encerradas em 16/10/2026. Mesmos 24 casos congelados, gabarito revisado v2 e política `mcp-sentry-review-v2`; cada configuração tem R1/R2 = 48 revisões principais (26 legítimas e 22 maliciosas). R3 é diagnóstico separado. As tentativas técnicas originais são preservadas e exportadas fora das principais.

| Configuração | Acertos principais | Legítimas bloqueadas | Maliciosas permitidas | Inconclusivas | R3 acertos/total | Técnicas excluídas |
|---|---:|---:|---:|---:|---:|---:|
| [gpt-6-luna low](13_evolucao_131_luna_low/README.md) | 34/48 | 13/26 | 0/22 | 1 | 2/4 | 1 |
| [gpt-6-luna medium](14_evolucao_131_luna_medium/README.md) | 44/48 | 4/26 | 0/22 | 0 | 1/2 | 0 |
| [gpt-6-luna high](15_evolucao_131_luna_high/README.md) | 46/48 | 2/26 | 0/22 | 0 | 2/2 | 0 |
| [gpt-6.1-sol low](16_evolucao_131_sol61_low/README.md) | 48/48 | 0/26 | 0/22 | 0 | 0/0 | 1 |

## Tempos e tokens das 48 principais

| Configuração | Soma dos turnos (s) | Mediana por revisão (s) | Tokens observáveis | Entrada sem cache | Saída |
|---|---:|---:|---:|---:|---:|
| gpt-6-luna low | 1465.618 | 20.6175 | 14147033 | 1657807 | 39690 |
| gpt-6-luna medium | 1449.837 | 20.9705 | 14480575 | 1580909 | 51410 |
| gpt-6-luna high | 1582.030 | 25.6465 | 14175492 | 1585690 | 75370 |
| gpt-6.1-sol low | 2419.064 | 41.0965 | 16641765 | 1814668 | 43993 |

Todos os tokens dos 602 turnos preservados foram reconciliados com os rollouts. Os CSVs e `tempos-e-consumo.json` de cada série incluem também R3 e técnicas separadamente, inclusive a tentativa técnica longa de Sol low. Não transformar tempos de etapas aninhadas do gateway em latência total; duração dos turnos inclui modelo e ferramentas, e tokens não equivalem a faturamento. Modelo hospedado, rede, cache e carga não foram isolados.

## Relação com 1.1.0 e limites

Na [campanha 1.1.0](COMPARACAO_LUNA_110.md), Luna low/medium/high registraram 36/48, 46/48 e 47/48; nesta 1.3.1 foram 34/48, 44/48 e 46/48. São observações descritivas: não atribuir a diferença isoladamente à versão Sentry. Sol low foi executado em outra série e não estabelece superioridade geral do modelo. Não há liberações de casos maliciosos nas quatro séries 1.3.1; isso não prova ausência geral de falhas de segurança.

A auditoria final conferiu modelo/esforço efetivos, três turnos separados, pedidos fixos, bloqueio inicial, escopo das ferramentas, referência/envelope e backend parado nas 192 principais e 8 R3. A inconclusiva de Luna low permanece na principal. Sua tentativa técnica usou PowerShell em lugar do MCP; a de Sol low não comprovou bloqueio inicial. Ambas foram preservadas e repostas com autorização já registrada; não houve reposições por parecer incorreto. Previews truncados limitam a comprovação da entrega integral do dossiê.

São 24 casos repetidos, não 48 casos independentes. As séries usam a mesma conta Windows com pastas/sandbox; isso não constitui isolamento entre contas. Os resultados desta bateria operacional são separados das evidências da pesquisa principal A/B/C1/C2/D e não alteram seus artefatos congelados.

## Replicação e proveniência

O [pacote 1.3.1](../../reproducao-experimentos/sentry-1.3.1/README.md) fixa wheel, referências compartilhadas, modelos, mensagens e ordem; inclui instruções de credenciais locais, checklist de auditoria e seleção explícita de tentativas. Uma nova máquina/conta/versão de runtime deve ser registrada como nova condição. O pacote foi validado estaticamente, sem outra campanha de modelos.

Cada série publica agregados, execuções/turnos anônimos, tempos do gateway e hashes de proveniência. IDs são independentes por série e a ordem pública não representa cronologia. Conversas, argumentos/retornos MCP, justificativas, credenciais, caminhos privados e mapa de IDs permanecem fora do repositório. Casos e gabarito já distribuídos no pacote de replicação devem permanecer fora do contexto e permissões do revisor.
