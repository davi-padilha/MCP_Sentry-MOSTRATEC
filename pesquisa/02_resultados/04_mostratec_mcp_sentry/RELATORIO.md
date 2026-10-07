# Resultados e comparação das baterias MCP Sentry

O experimento observou o bloqueio por integridade e mediu, separadamente, os
pareceres da IA do Codex sobre atualizações controladas de Filesystem, Git e
Donna. Foram concluídas duas baterias de 48 revisões primárias. A repetição
corrigida acrescentou uma R3 diagnóstica. Nenhuma variante foi aprovada para
execução durante as revisões.

## Método e condições

Cada bateria teve 24 variantes congeladas, com duas repetições por variante
em conversas novas. As 12 benignas vieram do pacote privado do operador; as
12 malignas foram escritas para o experimento pelos pesquisadores com auxílio
do Codex, adaptadas dos casos da FEICIT. As alterações atingem somente recursos
fictícios e contas de teste próprios. São casos controlados, não uma amostra
representativa de atualizações reais do ecossistema MCP.

As conferências diretas dos três casos de injeção por descrição não induziram
os efeitos extras nos agentes. Após primeiras recusas, houve reformulação
autorizada na criação e posterior congelamento. Os controles técnicos
demonstraram sequências explícitas, não sucesso da injeção. Essa limitação
acompanha a interpretação de suas classes esperadas nas duas baterias.

| Condição | Primeira bateria | Repetição corrigida |
| --- | --- | --- |
| Modelo efetivo | gpt-6.1-sol | gpt-6-luna |
| Raciocínio | medium | medium |
| Gateway | Sentry 0.8.1 | Sentry 0.9.1 |
| Contexto adicional | Protocolo anterior | Políticas de privacidade aceitas pelo operador |
| Revisões primárias | 48 | 48 |
| R3 diagnósticas | 0 | 1 |

O client foi Codex Windows 26.930.41038 (MSIX 26.930.4958.0). As referências
nativas permaneceram Git MCP 2026.8.18, Filesystem 2026.8.31 e Donna fonte
0.1.0, com provider de anexo corrigido antes da criação. Runtimes registrados:
Python 3.14.5, Node 24.14.1 e Git 2.54.0.windows.1. Não comparar essas execuções
com o piloto como se o aplicativo tivesse permanecido na mesma versão.

Modelo e esforço foram conferidos nos contextos das conversas. Memória estava
desligada. Cada revisão recebeu três pedidos separados: tarefa MCP normal,
revisão do bloqueio e registro do parecer. As duas baterias reutilizaram os
mesmos hashes de patches, pedidos, ordem sorteada (semente 20261005), dados e
dependências nativas. Código e estado eram restaurados antes de cada revisão.
Registrar `liberar` é uma recomendação; não aprova a versão nem inicia backend.

## Resultados primários

| Medida | Sol/médio + 0.8.1 | Luna/médio + 0.9.1 + políticas |
| --- | ---: | ---: |
| Execuções primárias | 48 | 48 |
| Benignas com parecer bloquear | 2/24 (8,33%) | 0/24 (0%) |
| Marcadas malignas com parecer liberar | 2/24 (8,33%) | 2/24 (8,33%) |
| Inconclusivas | 0/48 | 1/48 (2,08%) |
| Pares R1/R2 concordantes | 24/24 | 23/24 (95,83%) |
| Backend protegido iniciado | 0/48 | 0/48 |

Na repetição, 47 primárias têm parecer registrado. Desses, 45 concordam com o
gabarito histórico (95,74% entre os válidos). A cobertura de registro é 47/48.
Esse denominador deve acompanhar a porcentagem: o inconclusivo não desaparece
da bateria nem é substituído pela R3.

Os dois bloqueios de uma variante benigna da primeira bateria não se repetiram.
A auditoria havia identificado que o mascaramento interpretava literais como
`"password="` e deformava o diff, ocultando linhas/classes. A correção conserva
essas linhas; na nova combinação experimental, ambas as repetições registraram
`liberar`. Isso não estima o efeito causal isolado da correção ou do modelo.

As duas recomendações de `liberar` frente a rótulos históricos malignos têm a
mesma ressalva nas duas baterias: a variante devolve campos já presentes na
referência nativa da agenda. A política compatível aceita esses campos. Essa
contagem não comprova duas falhas de segurança. O gabarito foi preservado;
nenhuma classe foi reescrita para melhorar as métricas.

A primária inconclusiva da repetição recomendou textualmente `bloquear`, mas
enviou identificadores que não correspondiam à revisão corrente. Duas chamadas
de registro falharam com “revisão pendente inexistente”; nenhum parecer foi
persistido. É uma falha observada de registro, não liberação maliciosa nem
simples recusa de analisar. A R3 registrou `bloquear` e permanece diagnóstica,
fora das métricas principais. Não houve outras R3 nessa série.

Os números por localização e tamanho da alteração estão em
[metricas_por_grupo.csv](metricas_por_grupo.csv). As taxas nesse CSV têm três
casas decimais, conforme o analisador; os valores nesta tabela foram calculados
diretamente das contagens.

## Tentativa parcial e correções técnicas

Uma tentativa de repetição com 0.9.0 foi encerrada após 12 execuções, três sem
parecer registrado. O esquema de `sentry_record_assessment` anunciava v1,
enquanto o dossiê e a validação exigiam v2. Houve também envio de hashes
inconsistentes depois de uma rejeição. Esses registros foram preservados e não
misturados às 48 primárias da série corrigida.

A 0.9.1 usa `POLICY_VERSION` no esquema anunciado. A validação teve 91 testes,
com um ignorado; seis interfaces stdio e dois controles sintéticos de registro
via SDK MCP (`allow`/`block`) passaram sem executar os backends nativos.
Os 14 módulos da instalação coincidem com o wheel e a fonte.

O coletor recebeu correções rastreáveis, com cópias anteriores preservadas:
variáveis ausentes na tentativa parcial; comparação do texto persistido com o
mascaramento intencional; rótulo de versão herdado no relatório. Em uma
primária, a chamada havia retornado sucesso e o bloqueio estava persistido,
mas o coletor comparava justificativa/riscos sem considerar `safe_text`.
A coleta foi corrigida por conferência do registro, sem novo prompt ou
parecer. Hashes, identificador, política e decisão continuaram exigidos iguais.
Controles com hash ou decisão alterados foram recusados.

As correções da instrumentação não reformularam casos nem corrigiram recusas
ou erros do modelo. A falha verdadeira de registro continuou inconclusiva.
O [CSV de eventos](eventos_tecnicos.csv) diferencia os eventos técnicos.

## Integridade e compatibilidade

Nas 49 conversas da série corrigida, a auditoria confirmou os três pedidos,
modelo/esforço, ausência de chamadas fora do roteiro e preservação da aprovação
e do envelope. Após o encerramento, Git, Filesystem e Donna retornaram às
fotografias preparadas e a `doctor ready`. Fontes protegidas restauradas:
11 arquivos Git, 4078 Filesystem e 15 Donna. Catálogos: 12, 14 e 13 ferramentas.

Na primeira bateria, sete pedidos iniciais consultaram somente o diagnóstico
do Sentry, sem chamada à ferramenta protegida. Essa dificuldade foi preservada.
Zero inícios de backend não significa que toda conversa tentou uma chamada
nativa nem conta como acerto semântico da IA.

Nenhum MCP nativo foi removido ou modificado pela evolução do gateway. As
políticas são contexto de revisão, não filtro das respostas em execução.
A prova técnica anterior de equivalência de 36 leituras foi reutilizada;
ela não cobre exaustivamente todas as ferramentas e mutações nativas.

## Limites e acesso às evidências

- Gateway, políticas e modelo mudaram juntos: a comparação não isola cada
  fator nem demonstra superioridade geral de um modelo.
- R1/R2 repetem 24 variantes; não são 48 casos independentes.
- Persistem a ressalva do gabarito de agenda e os limites dos probes de injeção.
- Workspaces eram projectless, em pastas separadas com sandbox no mesmo usuário
  Windows. Isso não equivale a contas ou máquinas isoladas. O encaminhamento
  de mensagens inclui identificação da conversa de origem e até três pedidos
  recentes; essa condição foi registrada.
- O [registro público](execucoes_publicas.csv) omite gabarito por caso,
  justificativas, nomes originais, ordem e timestamps. O leitor pode recalcular
  inconclusivos e concordância; auditoria das classes requer o material privado
  do operador. Não usar estes dados como entrada das futuras revisões.

Os hashes em [proveniencia.json](proveniencia.json) vinculam os CSVs publicados
às fontes privadas consultadas. Transcrições, dossiês, patches, gabarito e
fotografias permanecem preservados fora do Git. Nenhum commit/push foi feito
pelo agente no fechamento destas séries.
