# Comparação — MCP Sentry 1.1.0 / GPT-6 Luna

Campanhas em 11/10/2026. Mesmos 24 casos com duas repetições, pedidos, políticas e gabarito v2. Fonte fixada no commit 518c705c004cfbf99f882fc288b35c60807549e0. Esforços medium, high e low confirmados nos rollouts.

| Indicador (R3 separadas das 48 principais) | Médio | Alto | Baixo |
|---|---:|---:|---:|
| Acertos | 46/48 (95,8%) | 47/48 (97,9%) | 36/48 (75,0%) |
| Malignas bloqueadas | 22/22 | 22/22 | 21/22 |
| Malignas liberadas | 0/22 | 0/22 | 0/22 |
| Benignas bloqueadas | 2/26 | 1/26 | 11/26 |
| Inconclusivas | 0 | 0 | 1 |
| Pares concordantes | 22/24 | 23/24 | 18/24 |
| Soma das durações dos turnos | 27min17s | 32min19s | 26min29s |
| Mediana por revisão | 25,669 s | 35,818 s | 25,285 s |
| Tokens totais | 13.774.570 | 13.513.125 | 14.379.794 |
| Entrada sem cache | 1.525.495 | 1.490.274 | 1.492.551 |
| Saída | 50.675 | 76.611 | 39.883 |
| R3 fora das 48 | 2 | 1 | 6 |
| Acertos dos R3 contra o gabarito v2 | 2/2 (100%) | 1/1 (100%) | 4/6 (66,7%) |

Alto: um acerto a mais que médio, duração acumulada 18,5% maior e tokens totais 1,9% menores. Baixo: dez acertos a menos que médio, duração acumulada 2,9% menor e tokens totais 4,4% maiores. Total de tokens não equivale a preço: alto produziu mais saída, e cache tem tratamento próprio. Não há cobrança monetária registrada.

R3 são diagnósticas e não substituem decisões R1/R2. Seus acertos são medidos contra o mesmo gabarito v2; as porcentagens usam apenas o número de R3 executadas, fora das 48 revisões principais. Luna baixo teve uma revisão maligna inconclusiva por duas tentativas incompatíveis de registro, sem recibo persistido; não houve liberação dessa variante.

Luna alto inclui uma reposição técnica autorizada de uma conversa que teve somente dois turnos porque o pedido de análise não foi confirmado antes do pedido de registro. A tentativa original foi preservada, sem apagar sua decisão ou consumo. A reposição, também com parecer de liberar, foi executada no final: a ordem temporal integral não foi preservada. As 48 revisões selecionadas passaram nas verificações estritas.

A tentativa técnica excluída acrescentou 22,763 s de turnos e 227.849 tokens. Não é parte das 48 nem das R3. O controle corrigido exige identificadores distintos e contagem de turnos antes de enviar o próximo pedido.

Duração de turnos inclui modelo e ferramentas; não inclui toda preparação/restauração. As etapas do gateway são aninhadas, não devem ser somadas novamente. A bateria mantém backends alterados parados e não mede ganho de reuso em uso normal. Mesma versão do cliente declarada na configuração; mesma conta Windows e separação por pastas/sandbox, sem usuário dedicado.

As prévias MCP truncadas limitam a comprovação da entrega integral de cada dossiê ao modelo. A auditoria operacional passou, mas não certifica entrega integral nem prova causal isolada de esforço/modelo.

Relatórios: [alto](11_evolucao_110_luna_high/README.md), [médio](10_evolucao_110_luna_medium/README.md), [baixo](12_evolucao_110_luna_low/README.md).
