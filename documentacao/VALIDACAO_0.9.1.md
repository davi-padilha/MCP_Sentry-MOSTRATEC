# Correção de protocolo da 0.9.1

A repetição com GPT-6 Luna/médio revelou uma incompatibilidade da 0.9.0:
`sentry_record_assessment` anunciava `mcp-sentry-review-v1` no seu esquema de
entrada, enquanto o dossiê e `submit_verdict` exigiam `mcp-sentry-review-v2`.
Clientes que obedeciam ao esquema anunciado recebiam “política ou decisão
inválida”. Isso não demonstra uma recusa nem um erro de classificação do modelo.

A 0.9.1 usa a constante `POLICY_VERSION` também no esquema anunciado. Mantém
as políticas de privacidade, o mascaramento corrigido, a validação dos hashes,
o requisito de leitura das evidências e a separação entre parecer e execução.
Não altera o código ou os catálogos dos MCPs nativos.

O teste de regressão consulta o catálogo, lê as evidências e registra decisões
`allow` e `block` usando a versão anunciada, em estados fictícios independentes.
A interface de revisão permanece sem objeto de backend. A suíte completa
executou 91 testes: passou, com um teste de plataforma ignorado.

Wheel: `pacote-usuario/mcp_sentry_gateway-0.9.1-py3-none-any.whl`.
SHA256: `94b51755b3246e8ee5d420f273bfbb1d50ca6e6c00c6e1307736f6219990a7e4`.

A série parcial `luna-090-20261006` foi preservada com 12 execuções, três sem
parecer registrado. Seu defeito técnico impede usá-la como bateria completa
ou interpretar essas falhas como erros de classificação. As conversas,
chamadas e respostas continuam disponíveis na área privada do operador.

A repetição corrigida foi concluída separadamente em `luna-091-20261006`, com os mesmos 24
patches, gabarito histórico, 48 posições sorteadas, três pedidos fixos por
conversa, recursos fictícios e políticas aceitas. Nenhum caso foi reformulado
em resposta aos pareceres. As séries anteriores e seus wheels permanecem
preservados. Foram concluídas 48 revisões primárias e uma R3 diagnóstica com
GPT-6 Luna/médio, confirmados nos registros. Nenhum backend protegido foi
iniciado. Os três servidores retornaram às fotografias preparadas e ao
diagnóstico `ready`.

As métricas históricas registram zero benignas bloqueadas, duas recomendações
de liberar em versões marcadas malignas no gabarito e uma primária inconclusiva.
As duas divergências têm a ressalva classificatória já documentada; o
inconclusivo permanece como resultado e a R3 não o substitui nas métricas.
A comparação muda gateway, políticas e modelo juntos, sem isolar seus efeitos.

O relatório completo, as conversas, a conferência de integridade e as correções
documentadas do coletor ficam na área privada do operador, em
`C:\MCP-Sentry-Mostratec\series\luna-091-20261006\operador\analise\`.
Os registros integrais continuam fora deste repositório. Uma seleção pública,
com relatório, métricas, eventos técnicos e execuções anonimizadas, está em
[resultados da MOSTRATEC](../pesquisa/02_resultados/04_mostratec_mcp_sentry/README.md).
Casos e gabarito histórico permanecem intactos e privados.
