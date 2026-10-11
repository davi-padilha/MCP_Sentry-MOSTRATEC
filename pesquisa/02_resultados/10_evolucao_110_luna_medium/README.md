# MCP Sentry 1.1.0 — Luna médio

Campanha autorizada por “ok para iniciar concedido” e concluída em 11/10/2026, horário de Brasília.
Fonte: branch otimizações, commit 518c705c004cfbf99f882fc288b35c60807549e0. Wheel SHA-256 b3f014c2431707f1d8780f245dddb803a1087bf6a3bdd5853225254419173f21.

## Resultado principal

| Indicador | Resultado |
|---|---:|
| Revisões R1/R2 | 48 |
| Acertos contra o gabarito v2 | 46/48 (95,8%) |
| Malignas bloqueadas | 22/22 |
| Malignas liberadas | 0/22 |
| Benignas liberadas | 24/26 |
| Benignas bloqueadas | 2/26 |
| Inconclusivas | 0 |
| Pares R1/R2 concordantes | 22/24 |
| R3 diagnósticas | 2, ambas liberar |
| Acertos dos R3 contra o gabarito v2 | 2/2 (100,0%) |
| Backend alterado iniciado | 0 |

As R3 não alteram as 48 métricas principais. Os dois bloqueios benignos permanecem como resultados da campanha.

## Auditoria operacional

O consolidador passou com os mesmos requisitos de vínculo, persistência, protocolo e proveniência da série 1.0, adaptado para 1.1.0 e 18 módulos.

- 50 conversas novas, com três pedidos por conversa: 150 turnos. Modelo gpt-6-luna e esforço medium conferidos nos rollouts; sem tokens herdados.
- Mesmos casos, ordem, pedidos, políticas e gabarito revisado v2. Sem aprovação ou execução de variantes.
- 48 pareceres principais persistidos e 48 recibos conferidos com o estado. Dois erros de registro foram recuperados pelo modelo na mesma conversa: 50 tentativas de registro principais, sem substituir conversas.
- Bloqueios iniciais comprovados, nenhuma chamada fora do roteiro, aprovações e envelopes preservados.
- 18 módulos idênticos entre fonte fixada, wheel e instalação.
- Git, Filesystem e Donna restaurados: doctor ready, sem issues. As 50 conversas foram arquivadas após a coleta.

## Comparação descritiva com 1.0.0 / Luna médio

| Indicador | 1.0.0 histórica | 1.1.0 atual |
|---|---:|---:|
| Acertos | 47/48 (97,9%) | 46/48 (95,8%) |
| Malignas liberadas | 0/22 | 0 |
| Benignas bloqueadas | 1 | 2 |
| Inconclusivas | 0 | 0 |
| Pares concordantes | 23/24 | 22/24 |
| Mediana da soma dos três turnos | 22,034 s | 25,669 s |
| Média da soma dos três turnos | 37,615 s | 34,098 s |
| Soma das durações dos turnos principais | 1.805,513 s | 1.636,724 s |
| Tokens totais principais | 14.697.656 | 13.774.570 |
| Tokens de entrada sem cache | 1.647.991 | 1.525.495 |
| Tokens de saída | 55.873 | 50.675 |

A duração acumulada caiu 9,3% e o consumo total de tokens caiu 6,3%; a mediana subiu 16,5%. A redução do tempo acumulado reflete menos revisões muito demoradas. Os arquivos não registram cobrança em reais ou dólares, portanto não permitem calcular a economia monetária efetiva no Codex. Nesta execução houve um bloqueio benigno a mais no agregado. A comparação é histórica: o Codex foi atualizado para MSIX 26.1007.2314.0, e a decisão da IA também pode variar entre conversas. Não isola causalmente o efeito do Sentry.

A bateria de alterações mantém todos os backends parados e não mede o ganho de reuso da cópia em tarefas normais. Duração de turnos inclui modelo, ferramentas e esperas internas; não é medida isolada da velocidade do Sentry.

## Tempos e tokens principais

- Mediana da soma dos três turnos: 25,669 s.
- Mediana do intervalo observado do primeiro ao último turno: 34,500 s.
- Entrada: 13,723,895 tokens; entrada em cache: 12,198,400.
- Saída: 50,675; raciocínio incluído na saída: 14,686.
- Total: 13,774,570. Cache e raciocínio não devem ser somados de novo.

Os tempos não incluem toda a preparação/restauração. R3 e tempos por etapa do gateway estão separados nos arquivos.

## Limitações e ajuste da coleta

O formato serializado do Codex atual apresentou prévias MCP truncadas em 16 das 50 conversas, contadas nos registros preservados. Isso limita a comprovação de entrega integral de cada dossiê ao modelo; a auditoria operacional não certifica essa entrega integral.

Na segunda conversa, o coletor antigo não reconheceu o parecer válido porque a prévia truncada não era JSON completo. Um coletor versionado passou a exigir review_binding completo, token terminal exato, recibo persistido e igualdade com o registro real. A conversa existente foi reapurada; nenhuma revisão foi repetida. Código do Sentry, prompts, casos e gabarito permaneceram congelados. Original e proveniência do coletor foram preservados no arquivo privado de auditoria.

Mantido o desenho anterior de pastas/sandbox no mesmo usuário Windows, sem conta dedicada. O caso historicamente reclassificado como benigno conserva sua limitação registrada no gabarito v2. São 24 variantes com duas repetições, não 48 casos independentes.

## Arquivos

- metricas_por_grupo.csv: métricas agregadas.
- execucoes_publicas.csv: 50 registros anônimos.
- turnos_publicos.csv: 150 turnos, tokens e tempos.
- tempos_gateway.csv: medições locais por etapa.
- tempos-e-consumo.json: agregados principais e diagnósticos separados.
- proveniencia.json: hashes e conferências.
A auditoria privada, as transcrições, os recibos e a comparação pareada permanecem fora do repositório público.

Esta pasta publica o relatório e as exportações anônimas da campanha. IDs HMAC independentes; gabarito por caso, patches, justificativas, credenciais e mapa das conversas permanecem privados.
