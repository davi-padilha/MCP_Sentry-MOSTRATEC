# Tokens e tempos das baterias históricas

Auditoria posterior dos arquivos de sessão, sem novas revisões ou execução de servidores.

Foram medidas **109 conversas e 327 turnos**: 48 primárias Sol 0.8.1, 48 primárias Luna 0.9.1, uma R3 Luna 0.9.1 e 12 conversas da tentativa parcial Luna 0.9.0.

Versão do CLI nos metadados: `0.160.0`. Versão do aplicativo registrada pelo operador: `26.930.41038`.
Período dos inícios das sessões (UTC): `2026-10-06T12:49:11.459Z` a `2026-10-07T01:58:21.511Z`. Apuração: 2026-10-07.

## Conferência

Todas as 109 sessões foram encontradas e tiveram identidade conferida. Conversas com ressalva na auditoria: **0**. O medidor emitiu 0 linhas de aviso.
Todos os turnos usam `turn_token_usage`; não houve fonte ausente ou inconsistente. Todas as sessões têm `derivada = nao`. A soma dos tokens dos turnos foi conciliada com o total de cada conversa, campo a campo: entrada, cache, escrita de cache, saída, raciocínio e total.

Os contextos dos 327 turnos confirmam `gpt-6.1-sol / medium` na série Sol e `gpt-6-luna / medium` nas séries Luna. Todas as durações estão presentes; não há intervalos negativos.

## Tokens por turno

Cada célula numérica apresenta **mediana / total**. Turno 1 = tarefa; 2 = revisão; 3 = registro. Tokens de raciocínio estão incluídos na saída; cache está incluído na entrada.

| Série | Uso | Turno | n | Entrada | Entrada sem cache | Saída | Raciocínio |
|---|---|---:|---:|---:|---:|---:|---:|
| luna_090_parcial | parcial_tecnica | 1 | 12 | 116.003 / 1.473.068 | 17.241,5 / 211.500 | 246 / 3.104 | 43 / 518 |
| luna_090_parcial | parcial_tecnica | 2 | 12 | 83.017,5 / 978.406 | 10.492,5 / 140.774 | 368,5 / 4.570 | 154,5 / 2.042 |
| luna_090_parcial | parcial_tecnica | 3 | 12 | 185.404 / 2.049.767 | 4.917 / 69.351 | 1.015,5 / 11.035 | 215,5 / 3.218 |
| luna_091 | diagnostico | 1 | 1 | 100.362 / 100.362 | 16.138 / 16.138 | 243 / 243 | 26 / 26 |
| luna_091 | diagnostico | 2 | 1 | 83.129 / 83.129 | 26.297 / 26.297 | 508 / 508 | 261 / 261 |
| luna_091 | diagnostico | 3 | 1 | 94.869 / 94.869 | 2.197 / 2.197 | 397 / 397 | 59 / 59 |
| luna_091 | principal | 1 | 48 | 103.788 / 5.429.530 | 18.370 / 878.106 | 234,5 / 11.538 | 38 / 1.926 |
| luna_091 | principal | 2 | 48 | 83.080 / 4.004.346 | 10.635,5 / 527.354 | 385,5 / 19.785 | 185,5 / 9.655 |
| luna_091 | principal | 3 | 48 | 94.230 / 4.794.711 | 2.438,5 / 128.087 | 421,5 / 22.095 | 62 / 3.851 |
| sol_081 | principal | 1 | 48 | 102.385,5 / 7.148.739 | 14.241,5 / 786.627 | 222 / 13.005 | 0 / 400 |
| sol_081 | principal | 2 | 48 | 115.867 / 5.125.900 | 10.652,5 / 558.220 | 326 / 15.785 | 20 / 941 |
| sol_081 | principal | 3 | 48 | 123.208 / 5.510.817 | 1.656,5 / 102.049 | 430,5 / 20.538 | 0 / 23 |

## Duração e intervalo entre turnos

Valores em segundos, **mediana / total**. A duração registrada inclui modelo, ferramentas, transporte e esperas dentro do turno; não mede apenas computação da IA. O intervalo antes do turno é um indicador de espera/acompanhamento do operador e aplicativo, sem atribuição causal exclusiva ao operador. O primeiro turno não tem intervalo anterior mensurável.

| Série | Uso | Turno | n | Duração registrada | Intervalo antes |
|---|---|---:|---:|---:|---:|
| luna_090_parcial | parcial_tecnica | 1 | 12 | 26,526 / 434,025 | — / — |
| luna_090_parcial | parcial_tecnica | 2 | 12 | 16,032 / 173,308 | 8 / 160 |
| luna_090_parcial | parcial_tecnica | 3 | 12 | 23,427 / 314,829 | 3 / 71 |
| luna_091 | diagnostico | 1 | 1 | 8,167 / 8,167 | — / — |
| luna_091 | diagnostico | 2 | 1 | 8,664 / 8,664 | 8 / 8 |
| luna_091 | diagnostico | 3 | 1 | 6,384 / 6,384 | 5 / 5 |
| luna_091 | principal | 1 | 48 | 13,055 / 1.057,363 | — / — |
| luna_091 | principal | 2 | 48 | 10,458 / 640,735 | 10,5 / 593 |
| luna_091 | principal | 3 | 48 | 10,017 / 489,937 | 4 / 222 |
| sol_081 | principal | 1 | 48 | 13,877 / 1.746,69 | — / — |
| sol_081 | principal | 2 | 48 | 14,184 / 974,266 | 11,5 / 29.589 |
| sol_081 | principal | 3 | 48 | 14,671 / 841,464 | 5 / 384 |

Na série Sol, **7 conversas** consultaram apenas `sentry_security_status` no primeiro turno. Mesmo assim, todas têm os três turnos previstos: trata-se de desvio no conteúdo da execução, não de formato ausente. Esse comportamento já registrado não altera os totais.

A série Sol contém **1 intervalo acima de cinco minutos**, com máximo de **28.538 s**. Ele foi mantido nos totais; representa uma pausa de acompanhamento entre turnos e não tempo de processamento do modelo. Por isso, o total de espera não deve ser usado como desempenho do gateway.

## Cache e tamanho dos dossiês

O tamanho é a soma dos caracteres dos conteúdos retornados por `sentry_review_current_block` no turno 2; não é contagem de tokens nem tamanho exclusivo do diff. Múltiplas leituras, quando presentes, são somadas. Zeros são informados separadamente.

| Série | Uso | Entrada total | Cache total | Cache / entrada | Dossiês > 0 / turnos 2 | Caracteres mín. / mediana / máx. |
|---|---|---:|---:|---:|---:|---:|
| luna_090_parcial | parcial_tecnica | 4.501.241 | 4.079.616 | 90,633% | 12 / 12 | 15.506 / 27.340 / 31.501 |
| luna_091 | diagnostico | 278.360 | 233.728 | 83,966% | 1 / 1 | 25.610 / 25.610 / 25.610 |
| luna_091 | principal | 14.228.587 | 12.695.040 | 89,222% | 48 / 48 | 15.506 / 23.400,5 / 32.066 |
| sol_081 | principal | 17.785.456 | 16.338.560 | 91,865% | 48 / 48 | 13.706 / 20.448 / 58.814 |

Na série Sol, há também **13 turnos fora do turno 2** com retorno de dossiê. Essas leituras entram nos tokens e tempos dos respectivos turnos, mas não na distribuição de tamanho acima, que atende ao recorte do turno de revisão. Os tamanhos positivos cobrem todos os turnos 2; não há zeros nessa distribuição.

## Medição, estimativas e limites

Tokens são contadores efetivos dos logs do Codex, usando o último contador acumulado de cada turno, uma vez por turno. Não se somam eventos cumulativos intermediários. Incluem contexto do aplicativo e resultados das ferramentas. Durações são os valores de `task_complete.duration_ms`; intervalos vêm dos horários de início e fim registrados.

Estes números não comprovam dinheiro debitado nem consumo dos limites da assinatura. Converter tokens em créditos ou dólares é uma estimativa dependente da tarifa e modalidade de cobrança. As estimativas históricas de Luna 0.9.1 permanecem em [TEMPOS-E-CONSUMO.md](TEMPOS-E-CONSUMO.md).

A tentativa parcial e a R3 estão separadas das primárias. As consultas antecipadas ao diagnóstico na bateria Sol não são excluídas nem reinterpretadas como novas revisões. O mapa, tabelas por sessão/turno e avisos detalhados permanecem privados. Nenhum resultado, gabarito, patch ou decisão foi alterado.

## Proveniência

- Medidor SHA-256: `ea6f7e68c6d7807a64e4448c140caaba50699546e1a7b405ea46faa9fce84d3e`.
- Consolidador SHA-256: `e2d5b060122900c4d35640331012b0e8dc20725a40c9ffc27e7cd48caaa7adfe`.
- Mapa privado SHA-256: `66b33229178f387ee7a733abcb536f68b60a9b8cca5f31ed25d0f12d7420afa1`.
- Tabela privada de sessões SHA-256: `68e11acc6e90ae86cfd64ceeaa9731c872d40a01e029a6fd73ae2ddbf2f48083`.
- Tabela privada de turnos SHA-256: `abe9819386437a216d6b12d0a27f66f97e593034f96488b19fb694fb8ffa7af8`.
- Auditoria privada SHA-256: `43552322e85de61e2a3ee8976958ae5b8e492302ab0a7e235976b24bbeefd833`.

- Registro privado `sol_081` SHA-256: `1ffc253fda9feb71effc0684d6e02ac820d031dcaceb9f7ced412a447c57aec9`.
- Registro privado `luna_091` SHA-256: `568f7956ce45d5712fa5b645719921bca54a914eb47ca17a61410b79bfe5ffc8`.
- Registro privado `luna_090_parcial` SHA-256: `2eb120986ff3e77312d275e565c0c1eedf89e0997b9b31871ca040504c2aa294`.