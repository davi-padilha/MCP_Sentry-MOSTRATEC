# Teste do MCP Sentry — tabela das duas baterias

Resumo para o relatório e o banner. Fonte: `pesquisa/02_resultados/04_mostratec_mcp_sentry/`
(`metricas_por_grupo.csv`, `execucoes_publicas.csv` e `RELATORIO.md`). Os resultados
das duas baterias são apresentados separadamente e **não** são comparados com os da
pesquisa da FEICIT.

## Como ler

- **Unidade:** uma revisão (variante + repetição). Cada bateria tem 24 variantes
  × 2 repetições (R1 e R2) = 48 unidades. R1 e R2 repetem as mesmas variantes;
  não são 48 casos independentes.
- **Malignas liberadas:** a IA registrou "liberar" numa variante marcada como maligna
  (o erro mais grave).
- **Benignas bloqueadas:** a IA registrou "bloquear" numa variante marcada como
  benigna (alarme falso).
- **Inconclusiva:** a IA não deixou parecer persistido.
- **Concordância:** pares R1/R2 com o mesmo parecer, sobre o total de pares.
- Cada variante vale 2 unidades. Em 12 variantes de cada tipo, **uma variante muda a
  taxa em 8,3 pontos**.

## As duas baterias

| | Bateria 1 (principal) | Bateria 2 (repetição corrigida) |
|---|---|---|
| Modelo / raciocínio | GPT‑6.1 Sol / médio | GPT‑6 Luna / médio |
| Sentry | 0.8.1 | 0.9.1 + políticas de privacidade |
| Revisões primárias | 48 | 48 (+ 1 R3 diagnóstica) |
| Client | Codex Windows 26.930.41038 | o mesmo |
| Datas | concluída em 06/10/2026 | concluída em 06/10/2026 |

Modelo, versão do Sentry e políticas mudaram juntos entre as baterias. A comparação
entre elas não isola nenhum fator e não indica qual modelo é melhor.

## Resultado geral

| Medida | Bateria 1 (Sol) | Bateria 2 (Luna) |
|---|---:|---:|
| **Backend protegido iniciado** | **0/48** | **0/48** |
| Malignas com parecer "liberar" | 2/24 (8,3%) | 2/24 (8,3%) |
| Benignas com parecer "bloquear" | 2/24 (8,3%) | 0/24 (0%) |
| Inconclusivas | 0/48 (0%) | 1/48 (2,1%) |
| Pares R1/R2 concordantes | 24/24 (100%) | 23/24 (95,8%) |

Nos 109 registros públicos (as duas baterias, a R3 e a tentativa parcial), o backend
protegido não iniciou em nenhum.

## Por onde a mudança está

| Grupo | Medida | Bateria 1 (Sol) | Bateria 2 (Luna) |
|---|---|---:|---:|
| **Só no código** (36 unidades) | Malignas liberadas | 2/18 (11,1%) | 2/18 (11,1%) |
| | Benignas bloqueadas | 2/18 (11,1%) | 0/18 (0%) |
| | Inconclusivas | 0/36 | 1/36 |
| | Pares concordantes | 18/18 | 17/18 |
| **Só na descrição** (12 unidades) | Malignas liberadas | 0/6 | 0/6 |
| | Benignas bloqueadas | 0/6 | 0/6 |
| | Inconclusivas | 0/12 | 0/12 |
| | Pares concordantes | 6/6 | 6/6 |

## Por tamanho da atualização

| Grupo | Medida | Bateria 1 (Sol) | Bateria 2 (Luna) |
|---|---|---:|---:|
| **Simples** (24 unidades) | Malignas liberadas | 0/12 | 0/12 |
| | Benignas bloqueadas | 0/12 | 0/12 |
| | Inconclusivas | 0/24 | 0/24 |
| | Pares concordantes | 12/12 | 12/12 |
| **Pequena**, 3 mudanças (12 unidades) | Malignas liberadas | 2/6 (33,3%) | 2/6 (33,3%) |
| | Benignas bloqueadas | 0/6 | 0/6 |
| | Inconclusivas | 0/12 | 0/12 |
| | Pares concordantes | 6/6 | 6/6 |
| **Grande**, 6 mudanças (12 unidades) | Malignas liberadas | 0/6 | 0/6 |
| | Benignas bloqueadas | 2/6 (33,3%) | 0/6 |
| | Inconclusivas | 0/12 | 1/12 |
| | Pares concordantes | 6/6 | 5/6 |

## Em número de variantes

Como as repetições concordaram nesses casos, os erros se concentram em poucas variantes:

| Ocorrência | Bateria 1 (Sol) | Bateria 2 (Luna) |
|---|---|---|
| Maligna liberada | 1 de 12 variantes malignas | 1 de 12 variantes malignas |
| Benigna bloqueada | 1 de 12 variantes benignas | 0 de 12 |
| Inconclusiva | 0 | 1 variante (uma repetição) |

Isso decorre dos próprios dados: nos grupos em que há erro, todos os pares R1/R2 foram
concordantes, então as duas unidades erradas são as duas repetições da mesma variante.
Os registros públicos são anônimos e não permitem apontar qual variante é.

## Eventos que acompanham os números

| Item | O que aconteceu |
|---|---|
| **Defeito de mascaramento (bateria 1)** | O mascaramento de segredos interpretava literais como `"password="` e deformava o diff. Os dois bloqueios de variante benigna ocorreram nessa condição. Corrigido na 0.9.1; na bateria 2 as duas repetições registraram "liberar". O efeito isolado da correção não foi medido |
| **Maligna rotulada como liberada (ambas)** | A variante devolve campos que a referência nativa da agenda já devolvia; a política compatível os aceita. O gabarito foi preservado, e a contagem não comprova uma falha de segurança |
| **Inconclusiva (bateria 2)** | A IA recomendou "bloquear" no texto, mas enviou identificadores que não correspondiam à revisão corrente. Duas tentativas de registro falharam e nenhum parecer foi persistido. A R3 registrou "bloquear" e fica fora das métricas |
| **Tentativa parcial (Sentry 0.9.0)** | 12 execuções, 3 sem parecer registrado: o esquema anunciado era v1 e a validação exigia v2. Série encerrada e preservada à parte; a 0.9.1 corrigiu |
| **Pedidos que não chamaram a ferramenta (bateria 1)** | Em 7 pedidos iniciais, a IA consultou só o diagnóstico do Sentry, sem chamar a ferramenta protegida |

## Limites da leitura

- 24 variantes por bateria, escritas para o experimento pelos pesquisadores com
  auxílio do Codex; não são uma amostra representativa de atualizações reais.
- As três variantes com injeção pela descrição não induziram o efeito nas
  conferências diretas. O gabarito "bloquear" delas se apoia no conteúdo do texto.
- Os workspaces eram pastas separadas com sandbox, no mesmo usuário do Windows.
- As taxas de malignas liberadas e benignas bloqueadas dependem do gabarito
  privado; os registros públicos permitem recalcular apenas inconclusivas e
  concordância.
- Os resultados valem para o Codex, os modelos, as versões do Sentry e os três
  servidores testados.
