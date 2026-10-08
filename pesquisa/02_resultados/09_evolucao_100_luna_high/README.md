# MCP Sentry 1.0.0 — Luna High

Coleta nova autorizada pelo pedido “Agora faça exatamente os mesmos testes com
Luna high”, iniciada e encerrada em 07/10/2026, horário de Brasília. As séries
Low e Médio e as tentativas canceladas foram preservadas.

Foram concluídas e arquivadas 48 conversas principais com os títulos exatos
**Teste v1 Luna High 1** até **Teste v1 Luna High 48**, mais uma conversa
**Teste v1 Luna High R3 1**, diagnóstica e fora do denominador principal.
Os 49 títulos e o arquivamento foram conferidos pela listagem do aplicativo.

## Resultados principais

| Resultado | Quantidade |
|---|---:|
| Revisões principais | 48 |
| Malignas bloqueadas | 22 de 22 |
| Malignas liberadas | 0 de 22 |
| Benignas liberadas | 25 de 26 |
| Benignas bloqueadas | 1 de 26 |
| Inconclusivas | 0 |
| Pareceres e recibos principais conferidos | 48 |
| Concordância com o gabarito | 47 de 48 (97,9%) |
| Pares R1/R2 concordantes | 23 de 24 |
| R3 diagnósticas | 1, com parecer liberar |

Mesmos 24 casos, duas repetições, ordem, pedidos fixos, políticas, gabarito
revisado v2 e gateway 1.0.0 das séries Low e Médio novas. Alteraram-se o esforço
para `high` e os caminhos exclusivos da série. O gabarito contém 13 versões
benignas e 11 malignas; nenhuma variante foi aprovada para execução.

## Auditoria

**O consolidador estrito passou**, sem relaxar seus requisitos. O preparador
 e o consolidador foram ampliados para aceitar `high`; os controles existentes
foram mantidos. O gateway e os pedidos dos testes não foram alterados.

- `gpt-6-luna` / `high` confirmado nos 147 turnos das 49 conversas novas.
- Memória desligada; nenhuma conversa derivada ou com tokens herdados.
- Todos os bloqueios iniciais e os três pedidos por conversa conferidos.
- Nenhuma chamada fora do roteiro e nenhum backend alterado iniciado.
- Aprovações e envelopes preservados; recibos conferidos com persistência real.
- Uma revisão principal teve um erro de registro, recuperado pelo modelo na
  mesma conversa: 49 tentativas resultaram em 48 pareceres válidos. Não houve
  substituição de conversas para melhorar o resultado.
- Evidências coletadas e conversa arquivada antes da preparação seguinte.
- Os 16 módulos coincidem entre fonte, wheel e instalação.
- Git, Filesystem e Donna restaurados: `doctor: ready`, sem issues.

## Comparação descritiva

| Indicador principal | Low | Médio | High |
|---|---:|---:|---:|
| Malignas liberadas | 0 | 0 | 0 |
| Benignas liberadas | 14 | 25 | 25 |
| Benignas bloqueadas | 11 | 1 | 1 |
| Inconclusivas | 1 | 0 | 0 |
| Pares concordantes | 20/24 | 23/24 | 23/24 |
| Auditoria estrita | Não passou | Passou | Passou |
| Tentativas de registro principais | — | 53 | 49 |

Médio e High tiveram os mesmos totais de classificação, não necessariamente
as mesmas decisões por revisão. Esta coleta não demonstra vantagem de High
em acerto agregado. A série Low teve duas conversas sem bloqueio inicial
comprovado e três com chamadas fora do roteiro; essas limitações permanecem
na comparação. Uma bateria pequena não garante classificação infalível nem
prova causal isolada do efeito do esforço.

## Tempos e consumo principais

| Medida | Médio | High |
|---|---:|---:|
| Mediana da soma da duração dos três turnos | 22,034 s | 26,1665 s |
| Mediana do intervalo observado do primeiro ao último turno | 31 s | 36 s |
| Entrada | 14.641.783 | 14.757.493 |
| Entrada em cache | 12.993.792 | 13.093.632 |
| Saída | 55.873 | 77.386 |
| Raciocínio | 18.413 | 40.124 |
| Total | 14.697.656 | 14.834.879 |

Contagens efetivas `turn_token_usage`. Entrada em cache é parte da entrada;
 tokens de raciocínio integram a saída. Não somar essas parcelas novamente.
Os intervalos não incluem toda a preparação, restauração ou conferência dos
títulos. R3 permanece separada nos dados abaixo.

## Arquivos

- [metricas_por_grupo.csv](metricas_por_grupo.csv): métricas principais.
- [execucoes_publicas.csv](execucoes_publicas.csv): 49 registros anônimos.
- [turnos_publicos.csv](turnos_publicos.csv): tokens e tempos dos 147 turnos.
- [tempos_gateway.csv](tempos_gateway.csv): etapas locais instrumentadas.
- [tempos-e-consumo.json](tempos-e-consumo.json): agregados, com R3 separada.
- [proveniencia.json](proveniencia.json): hashes e conferências.

IDs HMAC independentes; a ordenação não representa a sequência da coleta.
Gabarito por caso, transcrições, patches, justificativas, credenciais e mapa
original permanecem privados. Nenhuma publicação externa foi realizada.
