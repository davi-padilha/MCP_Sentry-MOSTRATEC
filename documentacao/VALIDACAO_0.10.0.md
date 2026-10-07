# Validação do gateway 0.10.0

Esta evolução implementa quatro mudanças no plano de controle do gateway:

- `review_binding` reúne revisão, hash revisado, hash do dossiê e versão da política. Erros de vínculo retornam código e ferramenta para releitura; valores incorretos continuam rejeitados.
- `receipt` devolve o parecer efetivamente persistido, após mascaramento, com os mesmos vínculos. `execution_authorized: false` explicita que o parecer não autoriza executar o servidor.
- `reference_contract` apresenta somente as declarações da política aprovada. Não certifica o comportamento do servidor nem infere permissões a partir da saída observada.
- `timings_ms` separa integridade, montagem do dossiê, persistência das evidências e persistência do parecer. Eventos locais de desempenho não contêm código, argumentos, caminhos ou credenciais. Falha nesta telemetria opcional não desfaz um parecer persistido.

As medidas ficam fora dos hashes de integridade e do dossiê. O encaminhamento de respostas das ferramentas nativas não foi alterado. As validações de identidade, cobertura de evidências, aprovação humana e envelope de execução continuam obrigatórias.

## Verificação do pacote

A suíte completa executou 96 testes com sucesso, com um teste ignorado por limitação de symlink na plataforma. Uma execução anterior teve `WinError 5` transitório na substituição de um arquivo de fixture dentro do OneDrive; a execução completa seguinte passou. Este incidente técnico é separado dos resultados das revisões pelo modelo.

Os novos testes verificam recibos contra o arquivo persistido e mascarado, rejeição de identidade incorreta sem reparo automático, independência dos hashes em relação às medidas, falha de telemetria sem perda do parecer e contrato derivado somente da política aprovada.

Wheel: `pacote-usuario/mcp_sentry_gateway-0.10.0-py3-none-any.whl`.
SHA-256: `e898d0564eedc13d3d732aefea6ec23fca6f91c0179d43a6ad454d587b5e0854`.
Os 15 módulos do pacote instalado no laboratório conferem byte a byte com o wheel e o código fonte.

O SDK MCP validou as seis interfaces (execução e revisão de Git, Filesystem e Donna), os esquemas de resposta e os recibos de liberar e bloquear contra os arquivos persistidos. Consultas nativas de leitura `git_log`, `list_directory` e `consultar_agenda` tiveram sucesso. Os estados utilizados nesta conferência foram restaurados antes da preparação da série.

## Nova série

A série usa GPT-6 Luna com raciocínio low, 48 revisões R1/R2 dos mesmos 24 patches congelados e o gabarito revisado v2. Preserva a ordem, as solicitações e os dados fictícios. Eventuais R3 são diagnósticos separados. As séries anteriores permanecem preservadas.

O objetivo desta etapa é validar a evolução do protótipo. A mudança conjunta de gateway e configuração de raciocínio não permite atribuir diferenças a um único fator. Não se presume ganho de desempenho antes das medidas.

## Ponto de parada solicitado pelo usuário

Após a validação, o operador interpretou a mensagem como autorização para executar e concluiu uma revisão com Luna/low. O usuário esclareceu que esperava a parada antes da bateria. A execução foi interrompida; o segundo caso havia sido apenas preparado, sem conversa iniciada. A revisão concluída permanece preservada como execução anterior à autorização de início da futura bateria, sem ser apresentada como 48 testes concluídos. As referências foram restauradas e a autorização ativa de início foi retirada. A nova bateria de 48 deve ficar separada deste registro preliminar.
