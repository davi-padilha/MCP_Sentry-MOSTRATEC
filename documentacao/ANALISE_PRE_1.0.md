# Análise de funcionamento e preparação da versão 1.0

Análise em 07/10/2026 da fonte 0.11.0, dos testes existentes, da validação
técnica e dos registros das baterias. Não foram executados testes novos,
revisões de modelo ou servidores. O código, os estados, os patches, o
gabarito e os resultados anteriores não foram alterados.

## Conclusão e escopo da 1.0

A 0.11.0 já tem um fluxo funcional validado para ferramentas MCP de
servidores locais via stdio. Após o feedback do usuário, o escopo da 1.0 fica
concentrado em corrigir as dificuldades observadas nas baterias e validar o
fluxo usado no experimento. A análise inicial tratou aprimoramentos preventivos
como requisitos de lançamento de forma excessivamente abrangente.

Os achados estáticos de concorrência, interrupção e uso prolongado ficam
registrados para evolução posterior. Não foram incidentes da coleta e não
impedem, por si, o fechamento da 1.0 do protótipo. Se uma falha for reproduzida
no uso normal ou comprometer uma garantia declarada, sua prioridade deve ser
reavaliada. Mantêm-se os limites técnicos conhecidos, sem prometer maturidade
de produto comercial.

A 1.0 deve significar estabilidade do fluxo e das garantias declaradas no
escopo suportado. Não depende de o modelo acertar todas as classificações.
Também não significa proteção universal de MCP, certificação de privacidade,
sandbox ou autenticação humana. O modo opcional de autorização na conversa
continua dependendo da atestação do cliente e precisa manter esse limite
explícito. O modo externo pelo operador permanece a referência operacional.

## Como funciona hoje

1. O operador prepara um manifesto, escolhe arquivos, confere o catálogo e
   aprova a referência inicial e o envelope de execução. Essa descoberta
   inicial pode executar o servidor e exige autorização própria.
2. O cliente conecta duas interfaces: execução e revisão. A interface de
   revisão não possui objeto de backend; ela não pode executar ferramentas
   nativas ou promover a referência.
3. Uma chamada nativa provoca nova inspeção de arquivos e configuração.
   Mudança de implementação bloqueia a chamada antes do início do backend.
   O gateway oferece diagnóstico e evidências, sem classificar sozinho
   a alteração como benigna ou maliciosa.
4. O dossiê compara referência e versão corrente, mostra cobertura e políticas
   e é identificado por hashes. Código, descrições e propostas são dados
   não confiáveis; a política aprovada fornece os critérios do operador.
5. Após entrega completa das evidências na conexão, um token associa o parecer
   à revisão lida. O registro valida identidade, hashes, cobertura e validade.
   O recibo mostra o parecer efetivamente persistido, inclusive o mascaramento.
6. Um parecer `allow` deixa a versão aguardando decisão humana. Autorizar
   uma execução, aceitar uma referência permanente e promover o envelope
   são decisões distintas. A autorização de uso único é consumida antes do
   início do processo, inclusive se esse início falhar.
7. Antes de iniciar, o gateway recaptura, copia e verifica os arquivos; então
   negocia MCP e compara o catálogo anunciado. A ferramenta recebe os argumentos
   originais e sua resposta nativa não passa pelo filtro de privacidade.
   A política orienta revisão; não fiscaliza cada resposta em execução.

Na referência inalterada, um processo já iniciado pode atender chamadas
subsequentes. Novas chamadas continuam passando pelo controle de integridade.
Bloquear uma chamada não é uma sandbox para efeitos internos ou processos
de terceiros. Interpretador, dependências externas e estado confiado seguem
os limites documentados do protótipo.

## O que já está coberto e não precisa ser refeito agora

- Correção do mascaramento que deformava literais e o diff histórico.
- Vínculo da revisão, cobertura completa, expiração, recusa de token inventado,
  de outra conexão ou associado a uma alteração anterior.
- Separação entre parecer, autorização de uma execução e promoção da referência.
- Recibos conferidos contra a persistência, política aprovada separada da
  proposta e medições auxiliares fora dos hashes.
- Cópia verificada e recaptura antes do início, restrição dos caminhos,
  negociação e conferência de catálogo.
- Instalação assistida, status administrativo e restauração seletiva com backup
  e rejeição de conflitos.

A [validação 0.11.0](VALIDACAO_0.11.0.md) registra 107 testes técnicos, um
ignorado por limitação de symlink, controles com SDK e leituras nativas.
Essas evidências permanecem válidas para os mesmos bytes. Uma candidata
modificada precisará de regressão própria; não se deve reutilizar o resultado
antigo como se tivesse testado o pacote novo.

Nas baterias do mesmo gateway, Luna low acertou 39/48 e medium 47/48.
Não houve liberação de malignas nas 22 revisões malignas de cada condição.
Isso descreve o conjunto controlado; não comprova cobertura de ataques externos.
O bloqueio residual variou nas repetições e não demonstrou falha de isolamento.

## Ajustes e prioridades para o protótipo

| Ajuste | Evidência | Tratamento recomendado |
|---|---|---|
| 1. Erros de registro e clareza do schema | Observado: oito chamadas iniciais sem token em low, duas em medium; uma inconclusiva low. | Necessário: distinguir campo ausente, formato misturado, token inválido e revisão vencida. Orientar reenviar ou reler conforme o erro, preservando a rejeição. Conferir o schema efetivamente recebido pelo cliente antes de atribuir o problema ao `oneOf`. |
| 2. Contexto e limites do dossiê | Observado: bloqueios de benignas por falta de comprovação de caminhos/privacidade, embora a validação estivesse preservada. | Priorizar clareza na apresentação e contexto relevante verificável. Não exige construir um analisador estático completo. Não deduzir segurança automaticamente nem inserir classes esperadas ou nomes de casos. |
| 3. Sessões, encerramento e medição | Observado: reconexões durante fechamento da coleta, antes da revisão 33; tempos não isolam cliente e modelo. | Ajustar o fechamento verificável no roteiro da coleta. Preservar as medições existentes. Instrumentação detalhada de cliente/transporte pode ficar para depois; o incidente não demonstra que é preciso reescrever o encerramento do gateway. |
| 4. Serialização de todas as transições da revisão | Estático: criação e expiração de registros não compartilham a exclusão das submissões e aprovações. | Evolução posterior para uso concorrente. Não é requisito automático da 1.0; antecipar se houver reprodução que afete o fluxo suportado. |
| 5. Recuperação de persistência e consulta de recibo | Estático: estado e relatório são gravados em etapas separadas; interrupção pode deixar lock ou transição parcialmente concluída. | Evolução posterior de recuperação após falhas excepcionais. Manter execução bloqueada em estado incompleto. Nunca remover o marcador de consumo para restaurar uma autorização. |
| 6. Catálogo equivalente com ordem diferente | Estático: o catálogo é comparado como lista; reordenar ferramentas iguais provoca rejeição. | Melhoria pequena e útil, opcional para a 1.0. Se implementada, comparar por nome sem ignorar mudanças de conteúdo nem aceitar nomes duplicados. Não ocorreu nos servidores das baterias. |
| 7. Limites de trabalho e recursos da conexão | Estático: uma thread é criada por mensagem e todas são retidas até o fechamento; a leitura completa pode agregar todos os diffs sem limite de bytes. | Evolução posterior para conexões longas e grandes volumes. A apresentação atual deve continuar sem truncamento silencioso; novos limites não podem gerar token de leitura completa quando conteúdo foi omitido. |

### 1. Registro

Em `mcp_facade.py`, a validação reconhece os dois formatos, mas um conjunto
incompleto de campos gera `INVALID_REQUEST` sem instrução específica.
O retorno deriva `recoverable` somente da presença de uma ferramenta de
releitura. Isso confunde correção do payload com necessidade de nova leitura.

Recomendo códigos próprios, campos ausentes e instruções de recuperação
estruturadas, sem ecoar valores secretos. Quando o token válido ainda existe,
um campo de parecer ausente pode ser corrigido; quando a revisão mudou ou
venceu, a evidência deve ser relida. Os schemas de saída precisam anunciar
exatamente os novos campos. O formato legado deve continuar compatível.

### 2. Evidências

`core.inspect` oferece diff e cobertura de raízes, mas não um contexto
específico de validadores inalterados. O mecanismo de cobertura confirma
entrega das alterações, não que o modelo compreendeu todas as dependências.

O contexto adicional deve ser extraído sem executar o código, incluir origem,
versão e hash e fazer parte da identidade do dossiê. Deve permanecer claramente
não confiável. Onde a seleção não puder demonstrar cobertura semântica, registrar
o limite. Informar também situações em que mascaramento ou representação de
arquivos não permitem comparar toda a alteração. Não tratar referência
aprovada como certificação automática nem incerteza como ataque demonstrado.

### 3. Operação e desempenho

A limpeza atual encerra o processo e remove sua cópia; falhas de remoção já
são informadas. Não há evidência de que o incidente da coleta tenha sido
causado por esse método: o cliente reabriu conexões. O ajuste na orquestração
deve ficar separado do pacote do gateway quando pertencer ao cliente.

As medidas locais existem e devem ser preservadas. Um identificador de
operação/sessão ajudará a correlacionar as etapas; tempos de transporte e
cliente exigem instrumentação fora do núcleo. A longa pausa histórica do Sol
é outro exemplo de intervalo que não representa custo de processamento.

## Achados preventivos para evolução posterior

Os itens seguintes detalham oportunidades futuras, sem acrescentar requisitos
ao fechamento da 1.0 no ambiente controlado. Sua descrição mantém os riscos
identificados na fonte e não representa reprodução de uma falha.

### 4. Concorrência

`review.ensure_pending` faz a sequência verificar existência/criar sem lock
comum. `_expire_if_needed` também escreve o registro. Há locks exclusivos
para submissão e aprovação e um marcador permanente para consumo, mas eles
não serializam todos os escritores do mesmo registro. Portanto, há caminhos
em que leitores concorrentes podem escrever uma observação antiga após
uma transição mais recente. A escrita atômica de um arquivo evita bytes
parciais; não resolve esse tipo de disputa lógica.

Não constatei ocorrência na bateria. Em uma evolução para uso concorrente, recomendo testes técnicos
determinísticos de criação simultânea, expiração versus submissão e
aprovação/consumo concorrentes. O teste atual de duas chamadas protegidas
com uma autorização é importante, mas cobre outra fronteira.

### 5. Interrupções e resposta perdida

`submit_verdict` e `approve_review_execution` gravam o estado antes de
renomear o relatório temporário. Se a segunda etapa falhar, o estado pode
ficar concluído sem o relatório obrigatório. A execução segue bloqueada
quando faltam os relatórios exigidos; entretanto, reenviar pode encontrar
uma revisão já concluída. Um encerramento abrupto também pode impedir o
`finally` de remover os locks temporários de transição.

Uma evolução de recuperação deve definir estado de recuperação, consultar o parecer/recibo
existente e tratar interrupção em cada etapa. Repetir exatamente uma solicitação
pode devolver um recibo existente; enviar conteúdo diferente não deve
sobrescrever o parecer. O marcador de consumo é deliberadamente permanente
e não pode ser tratado como um lock obsoleto removível.

### 6. Compatibilidade do catálogo

`BackendSession._verify_backend_catalog` usa `observed != approved`, que
considera a ordem da lista de ferramentas. Mesmo nome, descrição e schemas
em ordem diferente são rejeitados. Esse comportamento não foi um erro das
baterias atuais; é uma fragilidade de compatibilidade identificada na fonte.

A comparação por nome deve manter a verificação de conteúdo integral de
cada ferramenta. Também convém aplicar a mesma validação de nomes únicos
ao manifesto manual, sem depender apenas da descoberta assistida.

### 7. Uso prolongado e evidências grandes

`StdioGateway.serve` guarda referências de todas as threads em `workers` até
o EOF. Uma conexão longa acumula essas referências e não possui limite de
requisições simultâneas. O timeout do backend já existe; não é necessário
introduzir retries automáticos de operações nativas, que podem ter efeitos.

A conveniência de leitura completa junta todas as páginas do dossiê. O limite
de itens por página não é um limite de bytes. A solução deve manter explícito
o que foi entregue e ainda falta. Alterações nos limites não podem produzir
tokens de leitura completa para respostas truncadas ou diffs omitidos.

## Melhorias que podem ficar depois da 1.0

- Cache persistente da cópia verificada: há lentidão observada no Filesystem,
  mas reutilizar cópias exige controles novos contra alteração e invalidação.
  Não é necessário introduzir essa complexidade para fechar a primeira versão.
- Redução de capturas repetidas na mesma operação: útil investigar, mantendo
  recaptura nas fronteiras de decisão e início. Não reutilizar uma inspeção
  antiga como autorização de execução.
- Expansão para HTTP, recursos, prompts, solicitações do backend ao cliente
  e versões adicionais de MCP: recursos novos, fora do escopo atual.
- Autenticação humana independente do cliente e maior isolamento do sistema:
  evolução de arquitetura. Manter o modo experimental de conversa opcional
  e seus limites claros é condição de uso, não evidência de autenticação.
- Retenção automatizada de históricos/telemetria: útil para uso prolongado,
  mas exige política própria. Não remover registros obrigatórios ou evidências
  das baterias para economizar espaço.

Os totais altos de entrada incluem contexto do aplicativo e resultados das
ferramentas e são majoritariamente cache. Não demonstram que todo esse volume
foi produzido pelo Sentry ou pode ser reduzido com corte de evidências.

## Critérios para gerar e fechar a 1.0

1. Corrigir as mensagens e a recuperação de preenchimento do parecer;
   melhorar a clareza do dossiê e ajustar o fechamento das conversas na coleta.
   O trabalho deve manter proporção com o protótipo e os problemas observados.
2. Validar as alterações com controles dirigidos e a regressão técnica já
   existente. Conferir bloqueio por mudança, rejeição de vínculo incorreto,
   recibo persistido e autorização humana separada. Não acrescentar uma
   campanha de carga ou falhas excepcionais como requisito desta versão.
3. Conferir o pacote instalado e as ferramentas dos três servidores usados,
   com dados fictícios, preservando argumentos, respostas e operações nativas.
   Confirmar atualização no ambiente do experimento sem apagar referências,
   políticas ou configurações alheias.
4. Documentar ambiente/Python efetivamente validados e limites de uso; ajustar
   promessas de suporte à evidência disponível, sem exigir uma matriz extensa
   de plataformas. Gerar candidata, congelar wheel/hash e conferir fonte,
   pacote e instalação.
5. Na bateria posteriormente autorizada, manter casos, políticas e gabarito
   congelados e registrar as mudanças de apresentação. Preservar todos os
   resultados, inclusive erros do modelo. Não é necessário atingir 100% de
   classificação para declarar estabilidade do fluxo do protótipo.
6. Fechar 1.0 com o fluxo validado e as dificuldades observadas tratadas.
   Uma falha técnica reproduzida que aceite vínculo inválido, perca parecer
   no uso suportado ou execute sem autorização exige correção. Os achados
   preventivos não reproduzidos permanecem no plano de evolução posterior.

## Fontes da análise

- [Validação técnica 0.11.0](VALIDACAO_0.11.0.md).
- [Diagnóstico low](../pesquisa/02_resultados/05_evolucao_011_luna_low/RELATORIO.md).
- [Comparação medium](../pesquisa/02_resultados/06_evolucao_011_luna_medium/COMPARACAO.md).
- [Tokens e tempos históricos](../pesquisa/02_resultados/04_mostratec_mcp_sentry/TOKENS_E_TEMPOS.md).
- [Controle MCP](../desenvolvimento/gateway/mcp_sentry_gateway/mcp_facade.py).
- [Registros e transições](../desenvolvimento/gateway/mcp_sentry_gateway/review.py).
- [Captura e dossiê](../desenvolvimento/gateway/mcp_sentry_gateway/core.py).
- [Execução, catálogo e conexão](../desenvolvimento/gateway/mcp_sentry_gateway/gateway.py).
- [Limites do pacote](../pacote-usuario/README.md).

Wheel analisado: `mcp_sentry_gateway-0.11.0-py3-none-any.whl`.
SHA-256 conferido:
`a3e16dcdca8b71ebe5569be9da5d924ef486325727269d006338c96acb58c8ba`.

Este documento propõe o fechamento; não anuncia implementações ou testes
novos como concluídos. Sem alteração de versão, commit ou push.
