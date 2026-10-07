# Evolução 0.11.0 — GPT-6 Luna / low

Bateria executada em 07/10/2026 após autorização humana: 24 versões,
duas repetições e quatro R3 diagnósticas para pares divergentes.
Os resultados principais usam exclusivamente R1/R2 e o gabarito revisado v2,
congelado antes desta coleta: 13 versões benignas e 11 malignas.

| Resultado principal | Quantidade |
|---|---:|
| Revisões | 48 |
| Malignas: bloquear | 22 de 22 |
| Malignas: liberar | 0 |
| Benignas: liberar | 17 de 26 |
| Benignas: bloquear | 8 de 26 |
| Inconclusivas | 1 de 48 |
| Pares R1/R2 concordantes | 20 de 24 |

Os 47 pareceres persistidos têm recibos conferidos. Não houve execução dos
backends alterados. Modelo `gpt-6-luna` e esforço `low` foram confirmados nos
156 turnos das 52 conversas; memória permaneceu desligada. Os três servidores
nativos e seus estados aprovados foram restaurados e ficaram `doctor: ready`.

- [RELATORIO.md](RELATORIO.md): interpretação, erros e limites.
- [metricas_por_grupo.csv](metricas_por_grupo.csv): agregados do analisador.
- [execucoes_publicas.csv](execucoes_publicas.csv): 52 registros anônimos, com R3 separadas.
- [turnos_publicos.csv](turnos_publicos.csv): contagens e duração dos 156 turnos.
- [tempos_gateway.csv](tempos_gateway.csv): etapas locais instrumentadas, sem timestamps ou argumentos.
- [tempos-e-consumo.json](tempos-e-consumo.json): agregados de tempos e tokens.
- [proveniencia.json](proveniencia.json): versão, hashes e conferências.

Os IDs anônimos não indicam ordem nem correspondem aos IDs de outras séries.
Gabarito por caso, patches, transcrições, justificativas, contas e credenciais
permanecem fora do repositório. A publicação anterior continua separada.
O exportador auditável é `desenvolvimento/teste_do_sentry/consolidar_serie_011.py`;
`--verificar` faz apenas leituras e valida o payload público em memória.
