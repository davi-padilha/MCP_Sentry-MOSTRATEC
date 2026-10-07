# Tempos e consumo da série Luna 0.9.1

Apuração posterior em 07/10/2026, sem novas revisões ou mudanças nos resultados.
Foram lidos os logs locais das 48 conversas primárias e da R3 diagnóstica,
identificados pelas auditorias privadas. Todas tinham três turnos concluídos
e contextos confirmando `gpt-6-luna` / `medium`.

## Tempo observado

| Medida das 48 primárias | Valor |
| --- | ---: |
| Soma do tempo operacional registrado em `tempo_min` | 49,965 min |
| Tempo operacional médio por revisão | 62,46 s |
| Mediana do tempo operacional | 47,04 s |
| Soma das durações dos turnos | 36,467 min |
| Média da soma dos três turnos por revisão | 45,584 s |
| Mediana da soma dos três turnos | 31,868 s |
| Percentil 90 da soma dos três turnos | 84,305 s |
| Menor / maior soma dos três turnos | 15,337 / 97,509 s |
| Média por turno, 144 turnos | 15,195 s |
| Mediana de tempo até o primeiro token, por turno | 2,155 s |

`tempo_min` inclui acompanhamento e espera do operador. A duração dos turnos
foi obtida de `task_complete.duration_ms` e inclui raciocínio, respostas,
chamadas MCP e esperas dentro do turno. Não é latência pura do modelo nem
overhead isolado do gateway. As somas dos três turnos foram conferidas contra
`duracao_turnos_segundos` das auditorias. O percentil usa interpolação inclusiva.
A R3, excluída da tabela, teve soma de turnos de 23,215 s.

## Tokens e estimativas de custo

| Contagem cumulativa das 48 primárias | Tokens |
| --- | ---: |
| Entrada total | 14.228.587 |
| Entrada em cache, incluída no total acima | 12.695.040 |
| Entrada sem cache | 1.533.547 |
| Saída total | 53.418 |
| Raciocínio, incluído na saída acima | 15.432 |
| Escrita de cache registrada | 0 |

Foi usada a última contagem `token_count.info.total_token_usage` de cada
conversa, uma vez por conversa. Não se somaram os contadores cumulativos
intermediários, nem se acrescentaram novamente tokens de raciocínio ou cache.
A maior entrada de uma requisição foi 54.852 tokens. Esses totais incluem o
contexto do aplicativo e os resultados das ferramentas, não só o diff.
Não incluem orquestração, criação dos casos, série parcial 0.9.0 ou outros chats.

Pelas [tarifas oficiais do Codex](https://learn.chatgpt.com/docs/pricing),
consultadas em 07/10/2026, o equivalente em créditos Standard é:

```text
(1.533.547 × 2,5 + 12.695.040 × 0,25 + 53.418 × 12,5) / 1.000.000
= 7,675352 créditos nas 48 primárias
```

A R3 acrescentaria 0,184362 crédito, totalizando 7,859714. No regime Fast de
créditos comprados, a tarifa seria o dobro. Os logs consultados não identificam
o regime de velocidade/cobrança; portanto, não se afirma consumo faturado nem
redução correspondente dos limites incluídos na assinatura.

Como referência hipotética, a [tarifa API Standard do GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
é US$ 0,10 por milhão de entrada, US$ 0,01 em cache e US$ 0,50 de saída.
Aplicada aos mesmos contadores, resultaria em aproximadamente US$ 0,307 nas
48 primárias. A R3 acrescentaria aproximadamente US$ 0,0074. Isso não é uma
fatura do experimento: tarifas API são separadas do consumo por assinatura.
Não há evidência de custo monetário efetivamente debitado por esta bateria.

## Melhorias propostas a partir dos diagnósticos

As propostas abaixo não foram implementadas neste fechamento e não alteram
as duas baterias preservadas:

1. **Registro mais fácil de preencher e recuperar:** fornecer um objeto de
   vínculo claramente separado do conteúdo não confiável, contendo revisão,
   hashes e política; erros com código estruturado e indicação de releitura
   do diagnóstico. Manter a rejeição de identificadores incorretos, cobertura
   incompleta ou estado alterado. Não corrigir silenciosamente o vínculo.
2. **Recibo auditável do parecer:** retorno estruturado com decisão e campos
   efetivamente persistidos/normalizados, para evitar comparação literal do
   coletor com textos que o gateway mascara. Sem expor segredos removidos.
3. **Diagnóstico do contrato de privacidade:** informar claramente quais campos
   são aceitos na referência e na política, ajudando a distinguir exposição já
   aprovada de ampliação. A validação do gabarito continua sendo responsabilidade
   do protocolo; não se modifica uma classe histórica para ajustar o resultado.
4. **Medição por etapa:** registrar duração de verificação de integridade,
   montagem/leitura do dossiê e persistência, com IDs de correlação e sem conteúdo
   sensível. Tokens e tempo do modelo precisam de integração com o client;
   não são observáveis integralmente pelo gateway sozinho.

Todas podem ser desenvolvidas na interface de controle e na instrumentação,
preservando argumentos, respostas e efeitos das ferramentas MCP nativas.
Compatibilidade, concorrência e manutenção do bloqueio devem ser verificadas
antes de fixar uma nova versão para outra série experimental.
