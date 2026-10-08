# MCP Sentry 1.0.0 — Luna Médio

Coleta nova autorizada pelo pedido “Agora execute exatamente os mesmos testes
com o modelo Luna médio”, realizada em 07/10/2026, horário de Brasília.
A série Low e as tentativas canceladas foram preservadas.

Foram concluídas e arquivadas 48 conversas principais com os títulos exatos
**Teste v1 Luna Médio 1** até **Teste v1 Luna Médio 48**, mais uma conversa
**Teste v1 Luna Médio R3 1**, diagnóstica e fora do denominador principal.
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
revisado v2 e gateway 1.0.0 da coleta Low nova. Alteraram-se o esforço para
`medium` e os caminhos exclusivos da série. O gabarito contém 13 versões
benignas e 11 malignas; nenhuma variante foi aprovada para execução.

## Auditoria

**O consolidador estrito passou**, sem relaxar seus requisitos.

- `gpt-6-luna` / `medium` confirmado nos 147 turnos das 49 conversas novas.
- Memória desligada; nenhuma conversa derivada ou com tokens herdados.
- Todos os bloqueios iniciais e os três pedidos por conversa conferidos.
- Nenhuma chamada fora do roteiro e nenhum backend alterado iniciado.
- Aprovações e envelopes preservados; recibos conferidos com persistência real.
- Cinco revisões principais tiveram um erro de registro cada, recuperado pelo
  modelo na mesma conversa: 53 tentativas resultaram em 48 pareceres válidos.
  Não houve substituição de conversas para melhorar o resultado.
- Evidências coletadas e conversa arquivada antes da preparação seguinte.
- Os 16 módulos coincidem entre fonte, wheel e instalação.
- Git, Filesystem e Donna restaurados: `doctor: ready`, sem issues.

## Comparação descritiva com Low

| Indicador principal | Low | Médio |
|---|---:|---:|
| Malignas liberadas | 0 | 0 |
| Benignas liberadas | 14 | 25 |
| Benignas bloqueadas | 11 | 1 |
| Inconclusivas | 1 | 0 |
| Pares concordantes | 20/24 | 23/24 |
| Auditoria estrita | Não passou | Passou |

A série Low teve duas conversas sem bloqueio inicial comprovado e três com
chamadas fora do roteiro. Essas limitações impedem tratar a comparação como
prova causal isolada do efeito do raciocínio. Os números são observações
nesta bateria pequena, não garantia de classificação infalível.

## Tempos e consumo principais

- Mediana da soma da duração dos três turnos: **22,034 segundos** por revisão.
- Mediana do intervalo observado do primeiro ao último turno: **31 segundos**.
  Não inclui toda a preparação, restauração ou conferência dos títulos.
- Entrada: **14.641.783 tokens**, dos quais **12.993.792 em cache**.
- Saída: **55.873 tokens**, incluindo **18.413 de raciocínio**.
- Total: **14.697.656 tokens**; entrada em cache não deve ser somada novamente.

Os tempos e tokens das R3 estão separados nos arquivos abaixo.

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
