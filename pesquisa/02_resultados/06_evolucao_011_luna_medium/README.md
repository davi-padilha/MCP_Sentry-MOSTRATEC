# Gateway 0.11.0 — GPT-6 Luna / medium

Bateria executada em 07/10/2026 após pedido humano explícito: os mesmos
24 patches, duas repetições, pedidos e ordem das séries anteriores.
Modelo/esforço foram confirmados nos 147 turnos das 49 conversas.
O gabarito revisado v2 foi congelado antes desta rodada e permaneceu intacto.

| Resultado principal | Quantidade |
|---|---:|
| Revisões principais | 48 |
| Acertos frente ao gabarito | 47 de 48 |
| Malignas: bloquear | 22 de 22 |
| Benignas: liberar | 25 de 26 |
| Benignas: bloquear | 1 de 26 |
| Inconclusivas | 0 |
| Pareceres persistidos com recibo conferido | 48 de 48 |
| Pares R1/R2 concordantes | 23 de 24 |

Uma R3 diagnóstica recomendou liberar o caso divergente; permanece fora
das métricas principais e não substitui o bloqueio original. Nenhum backend
alterado foi iniciado. As referências e os estados aprovados foram
restaurados: Git, Filesystem e Donna estão `doctor: ready`.

- [COMPARACAO.md](COMPARACAO.md): comparação com 0.9.1/medium e 0.11.0/low, diagnóstico e prioridades.
- [comparacao_transicoes.csv](comparacao_transicoes.csv): mudanças agregadas de resultado nos mesmos casos/repetições.
- [comparacao_proveniencia.json](comparacao_proveniencia.json): conferências de patches, pedidos, ordem e políticas.
- [metricas_por_grupo.csv](metricas_por_grupo.csv): resultados principais agregados.
- [execucoes_publicas.csv](execucoes_publicas.csv): 49 registros anônimos com R3 separada.
- [turnos_publicos.csv](turnos_publicos.csv): contagens dos 147 turnos.
- [tempos_gateway.csv](tempos_gateway.csv) e [tempos-e-consumo.json](tempos-e-consumo.json): medições locais e agregados.
- [proveniencia.json](proveniencia.json): versão, hashes e auditoria.

Somente campos permitidos foram publicados. Os IDs anônimos são independentes
por série e não indicam a ordem de execução. O mapa de casos, gabarito por
caso, patches, transcrições, justificativas, contas e credenciais ficam privados.
As publicações anteriores permanecem preservadas.
