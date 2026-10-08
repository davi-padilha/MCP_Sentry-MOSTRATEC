# Validação do MCP Sentry 1.0.0

Validação em 07/10/2026. Esta distribuição fecha o fluxo do protótipo para
ferramentas MCP locais via stdio. Não promete classificação infalível pela IA,
sandbox ou maturidade de produto comercial.

## Alterações da 0.11.0

- Campo de registro ausente e mistura de formatos recebem erros estruturados,
  campos necessários, formatos aceitos e orientação de correção. Não se
  substituem tokens, IDs ou hashes inválidos por valores presumidos.
- O diff passa de três para doze linhas de contexto. Cada mudança inclui
  hashes do arquivo aprovado e atual e explicita os limites da comparação.
  Orientações distinguem risco introduzido, comportamento anterior e limites
  de evidência. Essas informações integram o hash do dossiê.
- A coleta arquiva cada conversa concluída depois de salvar e conferir as
  evidências, antes de preparar outro estado. Isso é uma correção do roteiro
  do experimento, não uma alteração das respostas do MCP protegido.
- A pasta `instalar-mcp-sentry` reúne wheel, instalador, configuração, política
  de privacidade, solução de problemas e identificação da versão. Não requer
  acesso ao restante do repositório para instalar.

Argumentos, descrições e respostas das ferramentas nativas permanecem
preservados. A política continua sendo contexto de revisão, sem filtrar as
respostas do backend. Um parecer registrado não aprova uma execução.

## Controles técnicos

| Controle | Resultado |
|---|---|
| Suíte completa com a fonte 1.0 | 110 testes; 109 passaram e um foi ignorado por limitação de symlink no Windows |
| Três testes novos de registro/contexto em Python 3.14.5 | Passaram |
| Correspondência fonte, wheel e instalação | 16 módulos Python com bytes idênticos |
| Instalação limpa pelo PowerShell 5.1 | Passou, incluindo conferência de hash e versão |
| Upgrade do pacote 0.11.0 para 1.0.0 | Passou sem reaprovação dos MCPs |
| SDK MCP: Git, Filesystem e Donna | Schemas válidos e leituras nativas bem-sucedidas em dados fictícios |
| SDK MCP: registros sintéticos `allow` e `block` | Campo ausente recuperável, recibo igual ao persistido, backend alterado não iniciado |

A suíte completa e a instalação foram verificadas em Python 3.12.14; os
controles SDK usaram Python 3.14.5. O pacote declara Python 3.11 ou posterior,
mas isso não equivale a ter testado cada versão ou sistema operacional.

Um teste de fixture falhou com `PermissionError` em gravação dentro do
OneDrive. A mesma fonte e suíte passaram em pasta temporária fora da
sincronização. Não se enfraqueceu a gravação atômica do gateway. Durante a
validação do instalador foram corrigidas a dependência de `Get-FileHash` em
subprocesso PowerShell 5.1 e a transmissão de aspas para `python -c`; a versão
entregue passou depois dessas correções.

Os testes novos também conferem rejeição de hash incorreto, ausência de
persistência após registro inválido e inclusão das orientações no hash do
dossiê. A suíte anterior continua cobrindo tokens inventados, expirados,
vínculos de outra conexão e evidência incompleta.

## Identificação congelada

- Versão: **1.0.0**.
- Wheel: `mcp_sentry_gateway-1.0.0-py3-none-any.whl`.
- SHA256: `90c4f944160c03fbf90e9f7b1fc4777a86c567b9c223a92c2d08ce38c7cc4b4f`.
- Política: `mcp-sentry-review-v2`, mesmas regras por servidor da coleta 0.11.
- Gabarito: revisado v2, preservado na área privada.
- Casos: mesmos 24 patches, pedidos e ordem; duas repetições por configuração.
- Condições previstas para uma futura coleta: `gpt-6-luna`, raciocínio `low`
  e `medium`, com confirmação nos registros efetivos de cada conversa.

## Baterias do modelo

O usuário cancelou a tentativa parcial em 07/10/2026 e decidiu solicitar as
96 revisões em outro momento. Foram concluídas nove revisões com low e
preparado um décimo caso sem conversa iniciada. Medium não foi iniciado.
Essa tentativa foi excluída dos resultados finais; as evidências permanecem
somente na área privada, identificadas como coleta cancelada. Não foi
publicada uma bateria concluída nem calculada uma comparação 1.0 a partir
dessa amostra parcial. O código e os estados fictícios foram restaurados.

A distribuição 1.0 conserva a validação técnica acima. Após novo OK humano,
foi realizada uma coleta nova e separada com low: 48 conversas principais e
quatro R3, encerradas em 07/10/2026, horário de Brasília. Medium não foi
iniciado nesta solicitação. As 52 conversas foram arquivadas, com os títulos
principais `Teste v1 Luna Low 1` até `Teste v1 Luna Low 48` conferidos.

Os resultados observados foram zero malignas liberadas, 11 benignas
bloqueadas e uma inconclusiva; 20 de 24 pares concordantes. Há limites:
somente 46 bloqueios iniciais foram comprovados, e três conversas tiveram
chamadas fora do roteiro. O consolidador estrito recusou a coleta; seus
requisitos não foram relaxados. O relatório com as ressalvas está em
[07_evolucao_100_luna_low](../pesquisa/02_resultados/07_evolucao_100_luna_low/README.md).
Modelo e esforço foram conferidos nos 156 turnos. As três referências foram
restauradas e ficaram `doctor: ready`; não se observou execução de variantes.

R3, se houver discordância entre R1 e R2, será diagnóstica e não integrará
o denominador primário. Não se aprova nenhuma variante nessas revisões.

## Limites preservados

A inicialização do Filesystem continua custosa por copiar e conferir muitos
arquivos. Cache, tratamento ampliado de concorrência e recuperação após
interrupções excepcionais ficam para evolução posterior. Dependências não
declaradas, interpretador, proteção do estado e computador do operador fazem
parte das condições confiadas. Consulte o manual da distribuição para os
limites de instalação e autorização.

## Coleta nova 1.0.0 com Luna Médio

Após o pedido humano para repetir os mesmos testes com raciocínio médio,
foi concluída em 07/10/2026 uma série separada com 48 revisões principais e
uma R3 diagnóstica. Casos, pedidos, ordem, políticas, gabarito v2 e gateway
foram preservados; apenas esforço e caminhos exclusivos mudaram.

A auditoria estrita passou: 48 pareceres/recibos conferidos, zero malignas
liberadas, uma benigna bloqueada, zero inconclusivas e 23/24 pares
concordantes. Não houve chamadas fora do roteiro nem execução de variantes.
Modelo `gpt-6-luna` / `medium` confirmado nos 147 turnos; cinco erros de
registro foram recuperados na própria conversa. Os 49 títulos foram
conferidos e as conversas arquivadas. As três referências foram restauradas,
com `doctor: ready`.

Relatório, comparação descritiva com Low e dados anônimos:
[08_evolucao_100_luna_medium](../pesquisa/02_resultados/08_evolucao_100_luna_medium/README.md).
A comparação conserva as ressalvas da coleta Low, cuja auditoria estrita
não passou; não demonstra um efeito causal isolado do esforço.

## Coleta nova 1.0.0 com Luna High

Após o pedido humano para repetir os mesmos testes com raciocínio high,
foi concluída em 07/10/2026 uma série separada com 48 revisões principais e
uma R3 diagnóstica. Casos, pedidos, ordem, políticas, gabarito v2 e gateway
foram preservados; apenas esforço e caminhos exclusivos mudaram.

A auditoria estrita passou: 48 pareceres/recibos conferidos, zero malignas
liberadas, uma benigna bloqueada, zero inconclusivas e 23/24 pares
concordantes. Não houve chamadas fora do roteiro nem execução de variantes.
Modelo `gpt-6-luna` / `high` confirmado nos 147 turnos; um erro de registro
foi recuperado na própria conversa. Os 49 títulos foram conferidos e as
conversas arquivadas. As três referências foram restauradas, `doctor: ready`.

O preparador e o consolidador aceitam agora high, sem relaxar os controles.
Relatório e dados:
[09_evolucao_100_luna_high](../pesquisa/02_resultados/09_evolucao_100_luna_high/README.md).
High e Médio tiveram os mesmos totais de classificação nesta coleta; isso
não demonstra vantagem de High nem classificação infalível.
