# MCP Sentry 1.1.0 — Luna baixo

Campanha autorizada e realizada em 11/10/2026. Modelo gpt-6-luna / low.
Fonte: branch otimizações, commit 518c705c004cfbf99f882fc288b35c60807549e0.
Wheel SHA-256 b3f014c2431707f1d8780f245dddb803a1087bf6a3bdd5853225254419173f21.

## Resultado principal

| Indicador | Resultado |
|---|---:|
| Revisões principais | 48 |
| Acertos | 36/48 (75,0%) |
| Malignas bloqueadas | 21/22 |
| Malignas liberadas | 0/22 |
| Benignas liberadas | 15/26 |
| Benignas bloqueadas | 11/26 |
| Inconclusivas | 1 |
| Pares concordantes | 18/24 |
| R3 fora das métricas principais | 6 |
| Acertos dos R3 contra o gabarito v2 | 4/6 (66,7%) |

Pareceres R3: liberar, liberar, liberar, bloquear, bloquear, bloquear. R3 não substituem as decisões principais.

## Auditoria operacional

O consolidador estrito passou para as revisões selecionadas, sem relaxar suas verificações.
Modelo/esforço, três pedidos, vínculos, persistência, recibos, bloqueios iniciais,
pacote de 18 módulos e restauração foram conferidos.
Pareceres principais persistidos e recibos conferidos: 47/48.
Conversas principais com erro de registro: 10;
erros de registro: 11; tentativas: 58.
Chamadas fora do roteiro: 0. Backends alterados iniciados: 0.
Três referências restauradas, doctor ready sem issues. 54 conversas arquivadas e conferidas.

## Tempos e consumo principais

- Soma das durações dos turnos: 1.589,294 s (26min29s).
- Mediana: 25,285 s; média: 33,110 s.
- Entrada: 14.339.911; cache incluído na entrada: 12.847.360.
- Saída: 39.883; raciocínio incluído na saída: 363.
- Total: 14.379.794 tokens.

Cache e raciocínio não devem ser somados novamente. Sem valores de cobrança monetária registrados.
R3 e etapas locais do gateway estão separadas nos arquivos.
[Comparação com Luna médio](../COMPARACAO_LUNA_110.md).

## Limitações e ocorrências

17/54 conversas selecionadas têm prévias MCP serializadas truncadas.
A auditoria operacional não certifica entrega integral de evidências ao modelo.
Mesmo coletor v2 da série média. Mesmos casos, pedidos, políticas e gabarito v2.
São 24 variantes com duas repetições, não 48 casos independentes.
A bateria não mede reuso em uso normal; tempos incluem modelo/ferramentas,
mas não toda preparação e restauração. Ambiente separado por pastas no mesmo usuário Windows.

Uma revisão maligna ficou inconclusiva: o modelo tentou registrar duas vezes com argumentos incompatíveis e não persistiu parecer. Nenhuma conversa foi repetida para melhorar o resultado. Seu R3 é diagnóstico e não altera o denominador principal.

## Arquivos

- [execucoes_publicas.csv](execucoes_publicas.csv)
- [metricas_por_grupo.csv](metricas_por_grupo.csv)
- [proveniencia.json](proveniencia.json)
- [tempos-e-consumo.json](tempos-e-consumo.json)
- [tempos_gateway.csv](tempos_gateway.csv)
- [turnos_publicos.csv](turnos_publicos.csv)

Exportações anônimas publicadas nesta pasta. Gabarito por caso, patches, justificativas, transcrições, credenciais e mapa de conversas permanecem privados.
