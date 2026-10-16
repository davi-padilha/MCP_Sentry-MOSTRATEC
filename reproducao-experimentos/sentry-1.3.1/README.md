# Replicação — MCP Sentry 1.3.1

Complemento da [bateria congelada compartilhada](../sentry-1.0/README.md). Clone o repositório completo: esta pasta depende de `../sentry-1.0/`, que fornece os 24 patches, baselines, manifestos/políticas v2, gabarito, ordem R1/R2, dados fictícios e ferramentas originais. **Não se instala o wheel 1.0.0**: este complemento instala seu wheel **1.3.1**, fixado por SHA256. O pacote compartilhado permanece intacto.

[Resultados publicados](../../pesquisa/02_resultados/COMPARACAO_SENTRY_131.md). Configurações repetidas: `gpt-6-luna` com `low`, `medium`, `high`, e `gpt-6.1-sol` com `low`. Cada série usa 24 variantes × duas repetições = 48 revisões principais; R3 somente para pares discordantes e fora das métricas principais. A infraestrutura portátil foi conferida estaticamente; não constitui outra campanha executada.

## Requisitos e diferenças entre ambientes

Origem: Windows x64, Python 3.14.5 com pip/venv, Node 24.14.1, Git 2.54.0.windows.1, Codex CLI 0.162.0-alpha.17.2. Consulte `AMBIENTE_ORIGEM.json` e os resumos das séries para as versões efetivas. Acesso aos modelos, seis interfaces MCP locais e Google Calendar/Gmail real são requisitos externos. Dependências Python fixadas são baixadas; não é um instalador offline. Filesystem inclui node_modules congelado: não atualizar com npm.

O inicializador usa venv Windows (`Scripts/*.exe`); **Linux/macOS não foram certificados**. Uma portabilidade para esses sistemas deve adaptar caminhos de executáveis e registrar a mudança antes da série. Registre SO, runtimes, Codex, data, modelo/esforço realmente usados, configuração de sandbox, diferenças de conta/fixtures Google, versão da política e hashes. Mudanças de modelos hospedados podem impedir reprodução literal. Hashes de aprovação locais diferem com os caminhos; bytes dos casos e política devem permanecer iguais. Não tratar esses resultados descritivos como 48 casos independentes ou como demonstração de superioridade geral.

## Preparação local

Comandos no PowerShell **dentro desta pasta**, usando uma pasta nova por série, fora do repositório. Exemplo Sol low; substitua modelo/esforço para as outras três configurações.

```powershell
py -3.14 -B scripts/bateria.py verificar
py -3.14 -B scripts/bateria.py inicializar --raiz C:\Sentry131-SolLow --modelo gpt-6.1-sol --esforco low
py -3.14 -B scripts/bateria.py checar-patches --raiz C:\Sentry131-SolLow
```

`inicializar --sem-instalar` serve apenas para inspeção estática: não permite congelar nem preparar revisões. A inicialização não edita o Codex global, não inicia conversas e não executa variantes. Cria um workspace vazio irmão (`C:\Sentry131-SolLow-revisor`); `--workspace` permite outro caminho novo fora do operador/repo. Pastas diferentes, sozinhas, **não estabelecem cegueira**: configure sandbox/permissões que impeçam o revisor de acessar código, patches, gabarito e evidências do operador, mantendo o gateway capaz de lê-los. Registre o mecanismo. Desative memórias e não exponha instruções do projeto ao revisor.

Leia e integre somente as seis entradas de `C:\Sentry131-SolLow\config\codex-fragmento.toml` ao perfil de teste. Preserve outras entradas; se os nomes já existem, use perfil separado. O perfil deve usar o modelo/esforço da série; o fragmento configura MCPs, não escolhe modelo. Reinicie conexões para captar mudanças entre casos. Não use um perfil em que conexões antigas continuem executando o código anterior.

### Donna com Google real

Siga os [requisitos e autenticação do pacote compartilhado](../sentry-1.0/README.md). Obtenha OAuth Desktop e habilite Calendar/Gmail em conta exclusiva para fixtures. Salve seu cliente em `C:\Sentry131-SolLow\credenciais\donna\credentials.json`; nunca o copie para o Git.

```powershell
C:\Sentry131-SolLow\instalacoes\donna\Scripts\python.exe -B ../sentry-1.0/scripts/autenticar_google.py --raiz C:\Sentry131-SolLow
C:\Sentry131-SolLow\instalacoes\donna\Scripts\python.exe -B ../sentry-1.0/scripts/preparar_recursos_google.py --raiz C:\Sentry131-SolLow --receptor receptor@example.invalid
```

O segundo comando cria dois eventos fictícios e três rascunhos, sem enviar email. Preserve **12/10/2026** nos eventos e na tarefa, mesmo numa réplica posterior. Não substitua por mocks nem altere scopes. Registre diferenças do receptor/conta, sem publicar endereços pessoais. Autorização para executar uma campanha/alterar essa conta deve existir antes dessas ações.

Confira as referências originais, manifestos e fixtures antes de aprovar localmente:

```powershell
py -3.14 -B scripts/bateria.py congelar --raiz C:\Sentry131-SolLow
```

Este comando confere os bytes do baseline e a versão 1.3.1 instalada, aprova somente os baselines e guarda fotografias locais. Nunca aprove uma variante, nem use accept-current ou liberação de execução durante as revisões. Os arquivos de `operador/congelamento-local.json` e `config.json` ficam privados e registram a nova condição. Antes de iniciar, verifique prontidão das seis interfaces; durante cada caso, o bloqueio da implementação alterada é obrigatório.

## Execução: três mensagens em três turnos

```powershell
py -3.14 -B scripts/bateria.py preparar --raiz C:\Sentry131-SolLow --numero 1
```

Execute `--numero 1` até `48`, na ordem congelada. A saída contém o ID privado, modelo/esforço e três mensagens. IDs, variante, gabarito e resumo de riscos **não são enviados ao revisor**.

1. Crie conversa vazia no workspace isolado e escolha o modelo/esforço da série. Envie somente a tarefa emitida pelo preparador; espere o turno terminar. A tarefa Git usa os três commits do repositório fictício; Filesystem lista a pasta permitida; Donna consulta o intervalo original.
2. Confirme a chamada MCP nativa, bloqueio `security_review_required` e backend parado. Se a chamada nativa estiver indisponível, preserve a tentativa como desvio técnico; não substitua por shell. Envie somente a mensagem fixa de revisão e espere o segundo turno terminar.
3. Envie somente `Registre o parecer.`; espere o terceiro turno terminar. A revisão/registro devem usar a interface de revisão correspondente. Confira recibo e registro persistido; ausência de registro após protocolo válido é **inconclusiva**, não justificativa para tentar obter acerto.
4. Preserve rollout/conversa, modelo/esforço de cada turno, chamadas/resultados MCP, bloqueio inicial, recibo, registro persistido, aprovação/envelope antes/depois e eventos de ciclo de vida. Colete antes de restaurar/preparar o próximo caso:

```powershell
py -3.14 -B scripts/bateria.py coletar --raiz C:\Sentry131-SolLow --id ID_DO_PREPARO
```

Preencha a linha de `operador/registro.csv` com o parecer **persistido**, `servidor_iniciado=nao`, inconclusivo vazio ou motivo explícito, duração e dificuldades. A coleta copia arquivos Sentry; **não exporta conversas nem audita automaticamente sua aderência**. O checklist detalhado está em [AUDITORIA.md](AUDITORIA.md).

Preserve sempre tentativas originais. Reposição somente por impedimento técnico comprovado e autorizado (por exemplo modelo errado, shell no lugar do MCP ou turno não realizado); não por bloqueio excessivo, parecer incorreto ou inconclusiva semântica. Reponha a mesma posição antes de avançar, quando viável, documentando qualquer diferença de ordem. Não edite os pedidos, patches, política ou gabarito para melhorar desempenho.

R3 é outra conversa completa e só ocorre após divergência entre R1/R2 selecionadas. Prepare com o harness original, **após conferir os caminhos locais e encerrar conexões do caso anterior**:

```powershell
py -3.14 -B ../sentry-1.0/scripts/preparar_revisao.py --config C:\Sentry131-SolLow\operador\config.json preparar --versao F1 --repeticao R3
```

`F1` é exemplo: use somente o caso discordante. O harness não verifica essa condição; cabe ao operador. Use os mesmos três pedidos, modelo/esforço e coleta. Não misture R3 com as 48 principais.

## Auditoria e seleção sem apagar tentativas

```powershell
py -3.14 -B scripts/selecionar.py modelo --raiz C:\Sentry131-SolLow --plano C:\Sentry131-SolLow\operador\selecao.json
```

Depois de todas as tentativas, preencha esse plano **privado** mediante leitura das fontes (não por suposição): três IDs de turnos concluídos distintos, modelo/esforço, verificações, arquivos de evidência e respectivos SHA256. Use `principal`, `R3` ou `tecnica_excluida` em cada tentativa. Exclusão exige motivo técnico e referência à autorização. Não há escolha automática do melhor resultado. Erros e inconclusivas válidas permanecem nas principais.

```powershell
py -3.14 -B scripts/selecionar.py selecionar --raiz C:\Sentry131-SolLow --plano C:\Sentry131-SolLow\operador\selecao.json --saida C:\Sentry131-SolLow\operador\registro-selecionado.csv
py -3.14 -B ../sentry-1.0/scripts/analisar.py resultados --registro C:\Sentry131-SolLow\operador\registro-selecionado.csv --gabarito ../sentry-1.0/operador/gabarito.csv --saida C:\Sentry131-SolLow\operador\metricas.csv
py -3.14 -B scripts/bateria.py restaurar --raiz C:\Sentry131-SolLow
```

O seletor valida estrutura, hashes, 48 posições únicas, destinação de todas as tentativas e R3 exatamente para pares discordantes. Os campos de auditoria são **declarações manuais**, não um parser automático de rollout. Exige recibo conferido para parecer conclusivo; aceita ausência de recibo devidamente marcada em inconclusiva. O CSV integral e o plano nunca são sobrescritos. O analisador antigo lê uma tentativa por posição; **não o alimente diretamente com registro contendo reposições**, pois ele pode sobrescrever decisões de mesma posição em memória.

## Tempos, tokens e publicação

A ferramenta [medir_tokens_rollouts.py](../../desenvolvimento/avaliacao-sentry/medir_tokens_rollouts.py) lê os rollouts Codex sem publicar texto. Registre todos os turnos e custos das reposições, separando principal/R3/técnicas. Some tokens observáveis por turno; registre cache e entrada sem cache, sem interpretar tokens como custo faturado. Não transforme token ausente em zero. Tempos de etapas do gateway são aninhados; não devem ser somados como latência total. Não compare latência como se controlasse rede/carga/serviço hospedado.

`exportar_resultados.py` é o exportador histórico das **quatro séries encerradas**: depende das evidências privadas, manifestos de encerramento e layouts do operador original. Não é runner nem exportador genérico de nova réplica. Para novas réplicas, preserve as mesmas listas de campos públicos (contagens, tokens, tempos, uso), uma tabela agregada por grupo e proveniência por hash. Mantenha mapa de IDs, transcrições, justificativas, argumentos/retornos MCP, credenciais e dados pessoais fora do repo. IDs públicos por série não permitem alinhar os casos às variantes.

`SHA256.json` cobre os arquivos deste complemento, exceto o próprio índice. `REFERENCIAS_COMPARTILHADAS.json` fixa o índice completo do pacote compartilhado e os materiais metodológicos. A inicialização confere ambos os pacotes; nenhum estado de aprovação antigo é transportado. Licenças de terceiros dos baselines são preservadas nos archives compartilhados.

## Compatibilidade documentada de finais de linha

O índice histórico `sentry-1.0/SHA256.json` declara CRLF em 23 textos, mas o Git os distribui em LF. Isso inclui o gabarito: original CRLF `594ef4262c20c709fea3d630ef3e79d28cafbcd508adc7e167647579b685ba8c`, distribuição LF `f04b378a450e7ba585c74e0d6978cdde6096f48acd04a9ec137ac67330bd48dd`. Conteúdo, ordem, rótulos e patches não mudaram. O verificador antigo estrito falha nesses textos; use o verificador deste complemento.

`COMPATIBILIDADE_EOL.json` lista individualmente os dois hashes. O novo verificador exige bytes exatos de uma dessas representações e comprova a transformação LF→CRLF para o hash histórico; não ignora divergências gerais. `REFERENCIAS_COMPARTILHADAS.json` fixa também os hashes efetivamente distribuídos dos materiais metodológicos. Nenhum arquivo ou hash do pacote antigo foi reescrito nesta publicação. Patches e archives mantêm os bytes originais, sem exceção de EOL.

[Validações realizadas e comandos de conferência](VALIDACAO.md).
