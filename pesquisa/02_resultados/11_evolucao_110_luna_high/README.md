# MCP Sentry 1.1.0 — Luna alto

Campanha autorizada e realizada em 11/10/2026. Modelo gpt-6-luna / high.
Fonte: branch otimizações, commit 518c705c004cfbf99f882fc288b35c60807549e0.
Wheel SHA-256 b3f014c2431707f1d8780f245dddb803a1087bf6a3bdd5853225254419173f21.

## Resultado principal

| Indicador | Resultado |
|---|---:|
| Revisões principais | 48 |
| Acertos | 47/48 (97,9%) |
| Malignas bloqueadas | 22/22 |
| Malignas liberadas | 0/22 |
| Benignas liberadas | 25/26 |
| Benignas bloqueadas | 1/26 |
| Inconclusivas | 0 |
| Pares concordantes | 23/24 |
| R3 fora das métricas principais | 1 |
| Acertos dos R3 contra o gabarito v2 | 1/1 (100,0%) |

Pareceres R3: liberar. R3 não substituem as decisões principais.

## Auditoria operacional

O consolidador estrito passou para as revisões selecionadas, sem relaxar suas verificações.
Modelo/esforço, três pedidos, vínculos, persistência, recibos, bloqueios iniciais,
pacote de 18 módulos e restauração foram conferidos.
Pareceres principais persistidos e recibos conferidos: 48/48.
Conversas principais com erro de registro: 0;
erros de registro: 0; tentativas: 48.
Chamadas fora do roteiro: 0. Backends alterados iniciados: 0.
Três referências restauradas, doctor ready sem issues. 50 conversas arquivadas e conferidas.

## Tempos e consumo principais

- Soma das durações dos turnos: 1.938,943 s (32min19s).
- Mediana: 35,818 s; média: 40,395 s.
- Entrada: 13.436.514; cache incluído na entrada: 11.946.240.
- Saída: 76.611; raciocínio incluído na saída: 39.911.
- Total: 13.513.125 tokens.

Cache e raciocínio não devem ser somados novamente. Sem valores de cobrança monetária registrados.
R3 e etapas locais do gateway estão separadas nos arquivos.
[Comparação com Luna médio](../COMPARACAO_LUNA_110.md).

## Limitações e ocorrências

16/49 conversas selecionadas têm prévias MCP serializadas truncadas.
A auditoria operacional não certifica entrega integral de evidências ao modelo.
Mesmo coletor v2 da série média. Mesmos casos, pedidos, políticas e gabarito v2.
São 24 variantes com duas repetições, não 48 casos independentes.
A bateria não mede reuso em uso normal; tempos incluem modelo/ferramentas,
mas não toda preparação e restauração. Ambiente separado por pastas no mesmo usuário Windows.

Uma tentativa original teve somente dois turnos, pois o pedido de análise não foi confirmado antes do pedido de registro. Foi preservada como falha de protocolo e substituída por uma reposição explicitamente autorizada, com três turnos e decisão também de liberar. A reposição foi executada ao final, como exceção documentada à ordem temporal original. Acrescentou-se a contagem separada da tentativa excluída: 22,763 s e 227.849 tokens. O histórico privado conserva o registro completo anterior e ambas as conversas. O primeiro preparo R3 foi bloqueado antes de criar a conversa; retomado após autorização explícita, sem repetir revisão IA.

## Arquivos

- [execucoes_publicas.csv](execucoes_publicas.csv)
- [metricas_por_grupo.csv](metricas_por_grupo.csv)
- [proveniencia.json](proveniencia.json)
- [tempos-e-consumo.json](tempos-e-consumo.json)
- [tempos_gateway.csv](tempos_gateway.csv)
- [tentativa-tecnica.json](tentativa-tecnica.json)
- [turnos_publicos.csv](turnos_publicos.csv)

Exportações anônimas publicadas nesta pasta. Gabarito por caso, patches, justificativas, transcrições, credenciais e mapa de conversas permanecem privados.
