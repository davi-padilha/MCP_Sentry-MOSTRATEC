# Análise de otimizações do MCP Sentry 0.9.1

Data: 07/10/2026. Escopo: análise, sem implementar otimizações, iniciar servidores, aprovar versões, alterar configuração MCP, aplicar patches ou fazer commit/push.

**Conclusão:** priorizar separar verificação de bytes e preparação de texto (P1), evitar trabalho repetido na entrega do dossiê (N1), acompanhar identificadores preenchidos pelo Sentry (T9), estudar reutilização estrita da cópia (P4) e melhorar status (U1). Ignorar formatação (T3), confiar em tamanho/data (P5) e juntar revisão/registro removendo consentimento separado (T8) são rejeitados. Nenhum ganho de acerto da IA foi demonstrado para mudanças de apresentação ou modelo.

**Estado de implementação (conferido no código da 0.11.0 em 07/10/2026):** implementadas T9, U1 e U2; U5 já existia; T3, T8 e P5 ficam fora por violarem garantias; as demais estão pendentes. A 0.10.0/0.11.0 também acrescentou recibo do parecer, contrato da política aprovada, erros com orientação de releitura e medição do tempo por fase, que não eram ideias numeradas desta análise. A medição mostrou 39,84 s de cópia e verificação num início de 44,70 s do Filesystem, o que reforça P1, P2 e P4.

**Atualização de 08/10/2026 (branch de otimizações, sobre a 1.0.0):** P4, P1 e N1 implementadas e P2 parcial, com testes de equivalência e medição antes/depois no mesmo computador. O Filesystem passou de 39,6 s para 7,5 s até o primeiro resultado e de 10,1 s para 6,2 s de trabalho do Sentry numa revisão de bloqueio (medianas). Detalhes, limites e reprodução na [seção 10](#10-implementação-de-p4-p1-e-p2-08102026).

## 1. Critério e proveniência

As garantias são requisitos de aceitação:

- **G1:** detectar mudanças em arquivos protegidos, configuração e catálogo antes de iniciar.
- **G2:** executar somente bytes verificados, sem arquivos extras na cópia.
- **G3:** evidência necessária integralmente recuperável pela IA.
- **G4:** parecer só recomenda; registro/decisão humana separados, sem liberação automática.
- **G5:** não aumentar malignas recomendadas para liberar nem benignas para bloquear.

Nas tabelas cada linha informa G1 a G5 nessa ordem: **P** = mecanismo preservável; **C** = depende da condição explícita; **E** = efeito sobre IA precisa de experimento; **V** = viola requisito. P não certifica toda a implementação atual. “ACEITA” é classificação da ideia, não autorização para implementá-la.

**Código** significa observado na fonte; **medição**, contagem executada nesta análise; **histórico**, dado publicado anteriormente; **estimativa**, fórmula/hipótese sem demonstração experimental. Não converter hipótese em ganho demonstrado.

Checkout inicial: HEAD `9b9208be12f33db50990b0d9102f900f04dc20d4`. Já havia alterações em `desenvolvimento/teste_do_sentry/CHECKLIST_REVISAO.md`, `documentacao/PLANO_MOSTRATEC.md` e o não rastreado `documentacao/TABELA_RESULTADOS_BATERIAS.md`; preservadas. Não foi encontrado AGENTS.md na raiz/pasta pai ou entre arquivos rastreados. Fonte principal: `desenvolvimento/gateway/`, versão 0.9.1 no pyproject.toml. Não presumir equivalência com outras cópias ou instalação ativa.

| Arquivo em desenvolvimento/gateway/mcp_sentry_gateway/ | SHA-256 do recorte |
| --- | --- |
| core.py | e7810c6a00a0ac4f18184cc17aca687cce7bdef1115b1e7471233a01eb054a51 |
| gateway.py | c2631e2f9f58b198727fbfaa6394ac90f73f3064db8e5c652d6d8a26d04832fc |
| review.py | b20dced19dc95652048f51f3f466cfc2e6c7c662a2a78463ed097b1f5f1273c5 |
| mcp_facade.py | a31b1e6cd95af2de86ef08407fa0d2a02c84f84787ef745a92401b6b293c385c |

**Davi:** review.py e mcp_facade.py ainda exigem identificadores fornecidos no parecer neste recorte. Isso não informa o estado de outra máquina/branch. T9 está em andamento conforme o operador informou. T1/T2/T4–T8/T10 e N1/N3/N6 encostam nessas interfaces: coordenar contrato e refazer linha de base após sua correção, sem edição concorrente. Nenhum módulo de produção foi editado.

## 2. Linha de base de tokens

### 2.1 Contagens medidas

[medir_otimizacoes.py](../desenvolvimento/teste_do_sentry/medir_otimizacoes.py) importa definições da fonte com bytecode desligado, sem construir gateway, chamar inspeções persistentes ou iniciar backend. Conta caracteres Unicode e bytes UTF-8 de JSON compacto com chaves ordenadas. [LINHA_BASE_OTIMIZACOES.json](LINHA_BASE_OTIMIZACOES.json) preserva resultado e hashes dos 14 módulos.

**Tokens estimados = caracteres/4**, aproximação de planejamento não calibrada para estes modelos/código/JSON. Não é tokenizer real nem margem estatística. Não foi observada a transformação de outputSchema, annotations, nomes e instructions em contexto pelo Codex. Ferramentas podem ser descobertas sob demanda. Estes números representam o que o Sentry oferece via MCP, não cobrança integral comprovada em todo turno.

| Componente | Caracteres medidos | Tokens estimados |
| --- | ---: | ---: |
| Quatro ferramentas de revisão, catálogo JSON | 6.669 | 1.667,25 |
| Catálogo com sentry_authorize_once | 8.233 | 2.058,25 |
| Instrução execution externa | 397 | 99,25 |
| Instrução review externa | 754 | 188,50 |
| Instrução execution pela conversa | 385 | 96,25 |
| Instrução review pela conversa | 873 | 218,25 |
| Revisão externa: catálogo + instrução | 7.423 | 1.855,75 |
| Revisão conversacional: catálogo + instrução | 9.106 | 2.276,50 |
| Wrapper por ferramenta protegida | 126 | 31,50 |

Totais são soma de componentes, sem inventar envelope do prompt. O modo combinado tem instrução de 386 caracteres; o setup usual configura execution/review separados.

| Ferramenta | Definição inteira | Só descrição | inputSchema | outputSchema |
| --- | ---: | ---: | ---: | ---: |
| sentry_security_status | 1.724 | 92 | 46 | 1.423 |
| sentry_review_current_block | 1.449 | 328 | 46 | 865 |
| sentry_review_evidence | 1.798 | 293 | 225 | 1.117 |
| sentry_record_assessment | 1.683 | 350 | 622 | 545 |
| sentry_authorize_once, opcional | 1.563 | 649 | 358 | 393 |

Definição inteira inclui outros campos/pontuação. Descrições das quatro ferramentas somam **1.063 caracteres**: mesmo apagá-las por inteiro só retiraria 265,75 tokens pela heurística, e apagá-las não é aceitável. T7 não tem ganho grande demonstrado.

### 2.2 Interface de execução

**Código:** StdioGateway.handle(tools/list) filtra sentry_* em execution; review anuncia apenas controles. Já não há duplicação dos controles entre as duas interfaces. MinimumMcp.tools_list conserva ferramentas aprovadas e acrescenta 126 caracteres a cada descrição.

Se **C** é o tamanho do catálogo aprovado serializado como `{"tools": [...]}` e **n** o número de ferramentas, execution oferece **C + 126n** caracteres de catálogo, mais instrução de 397 caracteres (externa) ou 385 (conversacional). C não foi medido: catálogos integrais dos estados nativos não estão no pacote público consultado.

**Histórico:** [RELATORIO.md](../pesquisa/02_resultados/04_mostratec_mcp_sentry/RELATORIO.md) publica 14 ferramentas Filesystem, 12 Git e 13 Donna. Pela fórmula, wrapper adiciona **1.764/1.512/1.638 caracteres**, ou **441/378/409,5 tokens estimados**. Não é contexto completo medido desses servidores. `--baseline` permite medir C na máquina instalada. Catálogo vazio de 12 caracteres na saída local significa baseline não fornecida; não representa Filesystem.

### 2.3 Dossiê pequeno e grande

**Não medidos nesta sessão.** O pacote público declara dossiês/transcrições privados; não oferece exportações pequenas/grandes. Não foram procurados/lidos/aplicados gabarito ou patches privados. Poucas linhas alteradas podem vir acompanhadas de catálogo/política extensos; tamanho da atualização não determina D.

**Código:** sentry_review_current_block entrega todas as changes, identificadores, metadata approved/current, configuration, coverage e privacy, removendo paginação. get_pending repete campos fixos em cada página. inspect inclui @manifest no diff, além de representar metadata/configuration/privacy separadamente; há potencial redundância adicional do catálogo.

Para exportações existentes, medir **D = len(JSON compacto do payload)** e estimar **D/4**, separando diffs/metadata/configuration/privacy. Não atribuir a T5 economia fixa de 50% do dossiê: catálogo é apenas uma parte e pode aparecer também no diff de @manifest.

MinimumMcp.tool_result devolve structuredContent e JSON textual em content: duplicação no transporte. Não está demonstrado que o Codex injeta ambas no modelo. Script conta payload/texto e envelope MCP separados; **não dobrar tokens como uso real**. Pode ler exportação da ferramenta ou reconstruir payload de registro existente; marca reconstruções/campos desconhecidos, sem tratá-los como retorno exato. Saída só contém contagens, nunca texto da evidência.

### 2.4 Tokens reais no Codex

**Sim, contadores agregados, sem atribuição automática ao Sentry.** A documentação oficial do [Codex App Server](https://learn.chatgpt.com/docs/app-server) descreve thread/tokenUsage/updated. Confirmou-se nesta máquina evento event_msg com payload.type=token_count no JSONL da própria sessão, em `%USERPROFILE%\.codex\sessions\AAAA\MM\DD\rollout-*.jsonl`. info.total_token_usage e info.last_token_usage contêm input_tokens, cached_input_tokens, cache_write_input_tokens, output_tokens, reasoning_output_tokens e total_tokens.

São contadores reportados pelo Codex, não chars/4. Incluem contexto geral/outras ferramentas; não isolam Sentry. Não foi verificada tela do app com custo por ferramenta/descrição. Percentuais de limite da conta não substituem tokens. Para atribuir economia, comparar turnos equivalentes com modelo/contexto/ferramentas controlados e separar entrada/cache/saída/raciocínio.

## 3. Linha de base de tempo

### 3.1 Os ~60 s publicados

**Histórico, uma amostra da 0.7.0:** [VALIDACAO_0.7.0.md](VALIDACAO_0.7.0.md), “Tempo completo de início e primeira chamada”: Filesystem normal, 0,465 s até initialize/tools-list, 60,783 s na primeira chamada, 61,249 s total. Bloqueado, 13,391 s total; após aceitar, 60,919 s. Primeira chamada inclui início adiado. O documento diz que 72,402 s anteriores tinham outro smoke concorrente, impedindo atribuição causal.

Não há separação das fases, estatística de desempenho ou medida da 0.9.1 atual. Subtrair bloqueado de normal não isola cópia/Node. Histórico: 4.075 arquivos; fechamento recente: 4.078. tempo_min do CSV público inclui três turnos e espera humana; não localiza esses 60 s.

### 3.2 Caminho observado na 0.9.1

Primeira chamada normal via execution, sem mudança:

1. StdioGateway._protected_call → MinimumMcp.call_tool → security_status → ensure_pending → inspect: captura/comparação/serialização e relatórios.
2. BackendSession.start → _verified_capture → inspect(return_capture=True): outra captura/relatórios e conferência do envelope.
3. _copy_and_spawn → capture: outra captura, hash global e envelope; copyfile de cada arquivo e releitura/hash do destino.
4. Popen, initialize, notifications/initialized, tools/list e comparação de catálogo real; depois chamada da ferramenta.

**São três capturas nesse caminho, não apenas duas.** Uso único acrescenta inspeções em consume_allowed_once. Chamadas posteriores ainda verificam status mesmo com processo aberto. Na revisão, security_status e get_pending inspecionam separadamente; cada página adicional repete inspect. Registro também recaptura via evidência/submissão.

| Fase | Local | Medição atual / método permitido |
| --- | --- | --- |
| Captura na inspeção | core.capture via inspect | Não medida no instalado; script mede capture sem inspect, que grava relatórios |
| Captura antes da cópia | gw._copy_and_spawn; há também _verified_capture | Não medida; segunda capture do script é aproximação com cache de texto quente, não execução do fluxo completo |
| Montagem do texto de cada arquivo | _capture_text/safe_text | Cache LRU de 32 MiB observado; script mede texto inclusivo/mascaramento/hash. Colunas texto/regex se sobrepõem |
| Cópia/diretórios | shutil.copyfile/target.parent.mkdir | NA: escreve, não executada nesta análise |
| Releitura/conferência | digest(target.read_bytes()) | NA no início real; --verified-copy mede releitura de cópia existente, enumera ausentes/extras/divergências |
| Início Node | subprocess.Popen | NA: inicia backend, não autorizado nesta análise |
| Handshake/catálogo/ferramenta | start/_round_trip/_verify_backend_catalog | NA; separar de Popen numa execução posteriormente autorizada |
| Outras despesas | Enumeração, baseline JSON, canon/hash global, diff, auditoria, IPC | NA; não atribuir tudo ao SHA-256 ou Node |

Snapshot incorpora texto de todos os arquivos e seu hash global serializa esse texto. inspect lê baseline inteiro. Mesmo após P1, contabilizar serialização/relatórios. _capture_text recebe bytes já lidos/hashados; cache poupa mascaramento no mesmo processo, não primeira leitura nem passagem entre processos.

### 3.3 Script somente de leitura e limite lógico

Na máquina dos estados instalados, operador escolhe caminhos; placeholders não são descobertos automaticamente:

```powershell
py -3 -B desenvolvimento/teste_do_sentry/medir_otimizacoes.py
py -3 -B desenvolvimento/teste_do_sentry/medir_otimizacoes.py --baseline 'C:\ESTADO\versao-aprovada.json' --dossier-small 'C:\EXPORTACOES\pequena.json' --dossier-large 'C:\EXPORTACOES\grande.json'
py -3 -B desenvolvimento/teste_do_sentry/medir_otimizacoes.py --manifest 'C:\ESTADO\manifest.json' --verified-copy 'C:\ESTADO\copias-verificadas\COPIA_EXISTENTE'
```

Script só lê/imprime, sem instalar, persistir store, construir BackendSession, aplicar variantes ou iniciar subprocessos. Duas captures opcionais medem cache de texto frio/quente, não cache de disco controlado. Total inclui texto; não somar tempos sobrepostos. Verificação da cópia é diagnóstico offline, não gate atômico de execução.

**Um script estritamente de leitura não pode medir escrita da cópia nem início real do Node.** Essas fases ficam NA. Numa futura execução operacional autorizada pelos pesquisadores, usar profiler externo/instrumentação temporária separada para entrada/saída das fases, sem alterar verificações. Esse desenho não autoriza execução agora. O lifecycle atual só mantém last_event/updated_at, sem histórico suficiente para recuperar todos os intervalos.

Registrar hardware/disco/antivírus/runtime/hashes/quantidade e bytes; primeira execução e seguintes em processos novos, com repetição, mediana/dispersão. Para P3 comparar workers/contenção. Não desligar antivírus nem substituir hashes por timestamps. Nenhum ganho percentual/em segundos foi demonstrado.

## 4. Limites atuais frente às garantias absolutas

Esta análise não certifica que 0.9.1 cumpre todo requisito em qualquer ambiente:

1. **Catálogo declarado versus real:** alteração do catálogo no manifesto muda @manifest e bloqueia antes do início. Catálogo anunciado pelo backend só é comparado em _verify_backend_catalog **depois de Popen/initialize**. Impedir chamada não significa impedir início. Catálogo dinâmico baseado em recursos externos não é conhecido integralmente antes de executar código; G1 absoluta exige delimitar declaração protegida/descoberta autorizada ou arquitetura adicional.
2. **Extras na cópia:** _copy_and_spawn cria UUID novo e verifica cada arquivo, mas não varre o destino inteiro ao final recusando extras plantados. Diretório novo não impede processo com escrita. P4 exige conjunto exato e proteção contra alteração entre conferência/execução.
3. **Evidência:** safe_text mascara segredos e usa replacement para bytes inválidos. Unified diff não é leitor geral de arquivos integrais/contexto não alterado/binários. G3 exige rota controlada de recuperação da evidência necessária sem expor segredos; resumo/hash não bastam.
4. **Autoridade:** store fora de project_root só separa caminho; não estabelece ACL contra agente. Autorização conversacional é atestação do client, explicitamente não autenticação humana. G4 forte exige estado/decisão protegidos pelo sistema operacional ou integração nativa; botão local sozinho não cria barreira.

Otimizações não podem ampliar esses limites. Condições de isolamento/imutabilidade precisam de prova no ambiente, não só expectativa.

## 5. Todas as ideias solicitadas

Arquivos abreviados abaixo pertencem a desenvolvimento/gateway/mcp_sentry_gateway/: **core**, core.py; **gw**, gateway.py; **facade**, mcp_facade.py; **rev**, review.py; **setup**, setup.py; **onb**, onboarding.py; **op**, operator.py. Experimentos E-A/E-B/E-C/E-D estão na seção 7. Ganho “não quantificado” significa ausência de medição de economia, não ganho presumido.

### 5.1 Tokens

| Ideia | Viabilidade no código | Ganho estimado/limite | G1/G2/G3/G4/G5 e condição | Classificação | Estado em 0.11.0 |
| --- | --- | --- | --- | --- | --- |
| T1 — Resumo e diff sob demanda | Parcial: facade.call_tool entrega tudo; rev.get_pending já pagina; faltam resumo/índice e recuperação de contexto por hash | Inicial D substituído por S; ganho final = D menos resumo e detalhes recuperados. Pode ser negativo | P/P/C/P/E. Resumo não conta como evidência lida; detalhes estáveis/recuperáveis, sinais/configuração/políticas presentes, sem truncamento. Conservar gate _evidence_read. E-A | PRECISA DE EXPERIMENTO | Pendente |
| T2 — Agrupar lockfiles/minificados/dependências | Possível em core.inspect/facade; agrupamento não existe | Reduz primeira apresentação, não necessariamente revisão inteira; não quantificado | P/P/C/P/E. Esses arquivos executam ou definem dependências; não isentá-los de hashes/revisão. Recuperação e gate de leitura completos. E-A por categoria | PRECISA DE EXPERIMENTO | Pendente |
| T3 — Ignorar espaços/comentários | Incompatível como exceção a capture/inspect, que usam bytes | Economia por omissão não aceitável | V/P/V/P/V. Viola G1; comentários/docstrings/strings/diretivas/indentação podem mudar instruções/execução. Omissão viola G3 e arrisca G5. Só marcar como possivelmente cosmético seria outra ideia experimental | REJEITADA | Não implementar |
| T4 — Sinais estáticos no topo | Camada auxiliar possível em core.inspect; detector da lista não existe | Pode reduzir busca/raciocínio, mas adiciona tokens; ganho líquido desconhecido | P/P/P/P/E. Ausência de sinal nunca prova benignidade; diff integral preservado, incerteza/linguagem explícitas, código tratado como dado. E-A | PRECISA DE EXPERIMENTO | Pendente |
| T5 — Catálogo como diferença | core.inspect/rev.get_pending/facade hoje entregam approved/current e manifesto em diff | Catálogo duplicado removido menos delta/referências/detalhes recuperados; C desconhecido | P/P/C/P/E. Preservar identidade, ordem, schema, descrições, annotations e acesso às duas versões; gate compara catálogo integral. Política não vira ruído. E-A | PRECISA DE EXPERIMENTO | Pendente |
| T6 — Ocultar revisão sem bloqueio | Exige sinal entre interfaces/processos; gw._initialize anuncia tools:{} sem listChanged; serve só responde | Teto bruto: catálogo de 6.669 ou 8.233 caracteres, descontando controles mínimos/refresh; tokens reais desconhecidos | P/P/C/P/E. Status/rota de recuperação disponíveis se refresh falhar; gate independe da visibilidade. Suporte deste app não comprovado. E-C + E-A | PRECISA DE EXPERIMENTO | Pendente |
| T7 — Descrições/instruções menores | Constantes de gw/CONTROL_TOOLS em facade; coordenar com Davi | 100 caracteres ≈ 25 tokens só se client os fornece ao modelo. Quatro descrições somam 1.063 caracteres | P/P/C/C/E. Manter aviso de evidência não confiável, política aprovada, consentimento de registro e decisão externa/autorização nova. E-A | PRECISA DE EXPERIMENTO | Pendente |
| T8 — Revisar e registrar num pedido | Tecnicamente viável, contrário às instruções de gw/facade e protocolo de pedidos separados | Uma mensagem/transição a menos; retentativas/tempo não quantificados | P/P/P/V/E. Conforme formulada, remove salvaguarda de consentimento separado: G4. Desenho futuro com confirmação humana separada antes da escrita é outra proposta e não elimina essa confirmação | REJEITADA | Não implementar |
| T9 — Sentry preenche identificadores | VERDICT_SCHEMA/submit_verdict ainda recebem review_id/reviewed_hash/dossier_hash/policy_version; Davi implementa | Evita transcrição de dois hashes de 64 caracteres mais ID/política e retentativas; principal ganho é registro confiável | C/P/C/P/C. Vincular ao dossiê entregue nesta sessão, não revisão mais recente; invalidar mudança/expiração e preservar leitura completa/consentimento/validação. E-B + E-A para registro | ACEITA COM CONDIÇÃO | Implementada (0.11.0, `review_token`) |
| T10 — Parecer idêntico reutilizado | ensure_pending já reutiliza registro vigente de mesma identidade; reuso histórico ampliado é novo | Evita avaliação quando elegível; taxa de hit/custo desconhecidos | C/P/C/C/E. Mesmo current_hash não basta: baseline/dossiê/política/cobertura/contexto/envelope/contrato equivalentes; não reciclar autorização/consumo. TTL e nova decisão humana quando exigidos. Viés do parecer anterior requer E-D | PRECISA DE EXPERIMENTO | Pendente |
| T11 — Menor para triagem/maior com risco | Sentry não chama API de modelo nem implementa sampling; modelo vem do client. API externa possível sem versão nativa, com nova orquestração | Triagem + modelo grande pode custar mais; preço, escalonamento e erros não medidos | P/P/C/P/E. Menor decidindo nos casos sem sinal pode perder ataque sutil; ausência de sinal não justifica liberar. Qualquer piora rejeita. E-D | PRECISA DE EXPERIMENTO | Pendente |
| T12 — Prefixo estável/cache | Ordem/campos estáveis em gw/facade são viáveis; montagem/roteamento/cache pertencem ao client/provedor | Possível redução de custo/latência, não de tokens lógicos/evidência; não quantificado | P/P/P/P/P preservando conteúdo. Separar prefixo fixo de evidência atual; nunca servir versão velha para obter cache; não garantir hit no Codex | ACEITA COM CONDIÇÃO | Pendente |

**T6/Codex:** a [especificação MCP negociada de 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) define tools.listChanged e notifications/tools/list_changed. A [documentação MCP do Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) confirma MCP, mas não comprova aqui refresh confiável dessa sequência no build instalado. config/mcpServer/reload do App Server é outra operação, não prova de tratamento da notificação. Gateway não a emite e review não recebe bloqueio por push. **Possível no protocolo; ausente no Sentry; suporte efetivo deste Codex pendente de teste.** Não foi instalado/configurado probe.

**T11 sem versão nativa:** serviço externo pode chamar APIs de dois modelos, aplicar política, expor recomendação e aguardar humano. Acrescenta credencial/custo/envio de dados e muda arquitetura. O MCP atual não permite simplesmente trocar o modelo que conduz a conversa. Usar grande em todos os casos mantém avaliador, mas não entrega a economia pretendida.

**T12:** [prompt caching oficial](https://developers.openai.com/api/docs/guides/prompt-caching) permite reutilização de prefixos compatíveis, inclusive definições de ferramentas. Isso não é medição de desconto no Sentry. T6 pode invalidar prefixo ao mudar catálogo; ordenar ferramentas ajuda sem congelar evidência.

### 5.2 Tempo

| Ideia | Viabilidade no código | Ganho estimado/limite | G1/G2/G3/G4/G5 e condição | Classificação | Estado em 0.11.0 |
| --- | --- | --- | --- | --- | --- |
| P1 — Hash primeiro, texto só quando necessário | Cache _capture_text já parcial; primeira captura monta tudo. Futuro core.capture/inspect e identidade do snapshot | Parcela decodificação/regex/texto inalterado; leitura/hash continuam. Limite: tempo de texto medido na capture; sem segundos atuais | C/P/C/P/C. Hash de bytes completos e lista/configuração/catálogo protegidos; recuperar texto dos mesmos bytes. Preservar identidade ou migrar contrato explicitamente; saída equivalente | ACEITA COM CONDIÇÃO | Implementada na branch (08/10) |
| P2 — Eliminar captura antes da cópia | _verified_capture descarta _capture disponível e _copy_and_spawn recaptura; redesign possível, remoção simples insegura | Custo de uma capture menos verificações substitutas obrigatórias; não traduzido em segundos | C/C/C/P/C. Transportar snapshot/hash autorizado; copiar/conferir bytes e conjunto, revalidar manifesto/envelope, detectar adições/remoções/corridas. Retirar sem substituto viola G1/G2. E-B | ACEITA COM CONDIÇÃO | Parcial na branch (08/10): reconferência mantida, só ficou mais barata |
| P3 — Hash paralelo | core.capture sequencial; threads/workers possíveis | Fração paralelizável; disco, arquivos pequenos, GIL/regex podem limitar/piorar. Sem ganho quantificado | C/C/P/P/P com resultado idêntico. Saída ordenada, todos erros propagados, hash parcial proibido, workers/memória limitados. E-B | ACEITA COM CONDIÇÃO | Pendente |
| P4 — Reusar cópia verificada | _copy_and_spawn cria UUID e close remove cópia; novo índice/ciclo de vida necessários | Evita escrita/criação, mantém leitura/hash da fonte e destino/enumeração; sem segundos | C/C/P/C/P com mesmos bytes. Conjunto exato/extras/links/junctions/manifest/envelope, proteção pós-checagem, não reusar estado produzido pelo backend nem autorização. E-B | ACEITA COM CONDIÇÃO | Implementada na branch (08/10) |
| P5 — Tamanho/data e full scan periódico | Implementável, incompatível com contrato | Economia omitindo conferência é inaceitável | V/V/P/P/P. Mesmo tamanho/mtime forjados escondem alteração: G1; destino adulterado pode escapar: G2. Estatística só ordena trabalho, nunca decide integridade | REJEITADA | Não implementar |
| P6 — Vigia prepara dossiê | Novo worker junto de core.inspect/rev; não existe hoje | Desloca trabalho, não elimina; pode aumentar I/O/descarte. Sem ganho medido | C/P/C/P/C. Vigia é dica, recaptura completa no gate, dossiê por hash e invalidação stale. E-B inclusive evento perdido | ACEITA COM CONDIÇÃO | Pendente |

Para P1/P2/P6, ler fonte depois sem conferir hash não pode preencher a evidência da captura antiga. P4 precisa recusar extras mesmo aparentemente inofensivos: podem influenciar resolução de módulos. P2 não pode dispensar detecção de adições na fonte só porque o arquivo adicionado não foi copiado.

### 5.3 Facilidade de uso

| Ideia | Viabilidade no código | Ganho esperado, não medido | G1/G2/G3/G4/G5 e condição | Classificação | Estado em 0.11.0 |
| --- | --- | --- | --- | --- | --- |
| U1 — Status | rev.security_status/public_security_status já expõem estado/parecer; CLI não tem status completo | Menos consulta/confusão; sem economia numérica | P/P/P/P/P. Mostrar versão aprovada/hash atual/pendência/parecer/autorização sem promover estado. status atual inspeciona/grava auditoria: não é estritamente sem escrita | ACEITA | Implementada (0.11.0, `mcp-sentry status`) |
| U2 — Desinstalar/restaurar só entradas | setup._replace_server_table/backup ajudam; _restore_config só restaura se arquivo inteiro ainda for o produzido | Recuperação sem perder edições posteriores; não medido | C/P/P/C/P. Merge por propriedade da entrada/valores instalados, conflito para humano, não sobrescrever. Restaurar conexão direta retira proteção e exige decisão humana explícita; nunca automático após falha | ACEITA COM CONDIÇÃO | Implementada (0.11.0, `restore-codex`) |
| U3 — Janela local/decisão fora do agente | op.decide já interage localmente; GUI/notificação novas | Consentimento/entendimento e G4 se houver isolamento real | P/P/C/C/P. Hash/versão/parecer visíveis, humano autenticado, store/IPC/capacidade de aprovação fora da escrita/controle do agente. Botão equivalente em MCP não resolve | ACEITA COM CONDIÇÃO | Pendente |
| U4 — Português simples | core.inspect/op.decide/facade têm campos/mensagens; renderização possível | Legibilidade; pode adicionar tokens, ganho não medido | P/P/C/P/E quando orienta IA/decisão. Detalhe/avisos preservados, sem “sem sinal = seguro”; resumo por IA não é autoridade. E-A e compreensão humana separada | PRECISA DE EXPERIMENTO | Pendente |
| U5 — Detectar MCPs do Codex | **Já existe**: setup._configuration/_eligible/_select_server/run_setup para TOML/stdio compatível | Evita cadastro nos formatos cobertos; benefício existente | P/P/P/P/P no fluxo atual. Ampliar camadas/URL/flags não autoriza migração silenciosa | ACEITA | Já existia |
| U6 — Claude Desktop no setup | stdio reutilizável; setup/codex_fragment/doctor específicos de TOML/Codex, falta adaptador JSON | Mais clients, não ganho demonstrado de tempo/tokens | C/C/C/C/E. Preservar env/entradas, duas interfaces, consentimento externo e paginação/schemas; qualidade no novo client. E-C + E-A | PRECISA DE EXPERIMENTO | Pendente |
| U7 — doctor com conexão real | onb.doctor estático; discover_tools/BackendSession executam processo e oferecem peças | Diagnóstico de handshake/runtime que ready não comprova | C/C/P/C/P para probe protocolar. Modo explícito separado, versão elegível/autorização exigida; sem ferramenta mutante, consumo silencioso ou início alterado não autorizado | ACEITA COM CONDIÇÃO | Pendente |

U6: [documentação oficial MCP de conexão local](https://modelcontextprotocol.io/docs/develop/connect-local-servers) descreve configuração JSON do Claude Desktop; sustenta adaptador, não equivalência experimental. U7 não foi executado: conexão real inicia servidor e ultrapassa esta análise.

## 6. Ideias novas encontradas na fonte

| Ideia | Observação/viabilidade | Ganho/limite | G1/G2/G3/G4/G5 e condição | Classificação | Estado em 0.11.0 |
| --- | --- | --- | --- | --- | --- |
| N1 — Snapshot estável por entrega, sem inspect em cada página | facade current_block/get_pending/ensure_pending repetem inspeção por página/status | Poupa capturas/JSON da baseline/gravações durante entrega; evidência igual, tempo desconhecido | C/P/C/P/C. Snapshot imutável por hashes, invalidar leitura/registro ao mudar; checagem fresca antes de registrar/autorizar/iniciar. Não misturar gerações. E-B | ACEITA COM CONDIÇÃO | Implementada na branch (08/10) |
| N2 — Identidade de bytes separada de texto | digest(canon(current)) incorpora todo conteúdo mascarado; baseline JSON grande | Reduz serialização/memória/hash global; leitura continua; não quantificado | C/C/C/P/C. Canon de nomes/hashes/manifesto/envelope completo; evidência por hash recuperável. Migração explícita de baseline/review_id, sem reaproveitar aprovação por conveniência. E-B | ACEITA COM CONDIÇÃO | Pendente |
| N3 — Exposição menor de schemas redundantes | facade anuncia outputSchema grande/repetido; client pode nem fornecê-lo ao modelo | Quatro outputSchemas somam 3.950 caracteres; não é economia garantida | P/P/C/C/E. Manter contrato MCP/validação no servidor e campos de consentimento/erro; primeiro medir exposição. E-C + E-A, coordenar com Davi | PRECISA DE EXPERIMENTO | Pendente |
| N4 — Aviso de proteção central, menos repetição por ferramenta | facade injeta 126 caracteres por ferramenta; gw já tem instructions | Teto bruto pela contagem publicada: Filesystem 1.764/Git 1.512/Donna 1.638 caracteres | P/P/C/C/E. Client deve conservar aviso em descoberta/compactação; agente não contorna bloqueio como erro. E-A + E-C | PRECISA DE EXPERIMENTO | Pendente |
| N5 — Permissão efetiva da cópia/store | core.external só separa pastas; gw sem varredura final de extras | Reforça G2/G4, pode acrescentar tempo; não aceleração prometida | P/C/P/C/P. Agente sem escrita, conjunto/bytes finais conferidos, runtime externo declarado; testar isolamento/corrida. E-B | ACEITA COM CONDIÇÃO | Pendente |
| N6 — Deduplicar resultado no contexto do client | tool_result tem structuredContent e fallback textual | Duplica transporte, não necessariamente tokens; zero economia se client já deduplica | P/P/C/P/E. Preferir dedupe no client; não retirar fallback indiscriminadamente, recomendado pelo MCP negociado. E-C + E-A | PRECISA DE EXPERIMENTO | Pendente |

N2/P1: apagar content muda current_hash/dossier_hash/review_id e pode invalidar auditoria/aprovação. Não reescrever evidência histórica para esconder migração. N5 é condição de segurança para reuso contra arquivos plantados, não detalhe cosmético.

## 7. Desenho dos experimentos

Nenhum experimento de otimização foi executado nesta análise. Scripts/fixtures futuros não são autorização para executar, alterar proteção ativa ou acessar material privado nesta sessão.

### E-A — Apresentação da evidência e acerto da IA

Para T1/T2/T4/T5/T7/U4/N3/N4/N6; T6/U6 após compatibilidade:

1. Fixar baseline **com correção de Davi concluída**, client/build, modelo, esforço, políticas, ferramentas, prompts, limites e hashes. Controle contemporâneo; não comparar tratamento com bateria antiga de outra versão/modelo.
2. Operador aplica as **mesmas 24 variantes congeladas**, sem recriar ataques/editar patches/expor gabarito ao revisor. Controle/tratamento em conversas novas, duas repetições por variante por braço: **48 + 48 = 96 revisões por ideia**. Uma ideia por vez; depois testar combinações, porque efeitos podem interagir.
3. Sortear/contrabalançar ordem, restaurar código/estado antes de cada revisão, impedir acesso a parecer antigo/relatório/gabarito. Manter pedidos separados e consentimento de registro. Não aprovar variantes para execução durante revisões.
4. Avaliador separado/operador mantém gabarito e calcula: malignas com recomendação liberar, benignas com bloquear, inconclusivos, falhas de registro, concordância R1/R2, pares gêmeos e estratos servidor/código/descrição/tamanho. Preservar rótulos históricos e ressalvas.
5. Distinguir **recomendação textual** de **parecer registrado**: T9 pode melhorar registro sem alterar análise. Erro de ID não vira automaticamente maligna liberada. Inconclusivos permanecem no denominador; R3 diagnóstica não substitui R1/R2.
6. T1/T2/T5: registrar detalhes recuperados, páginas/bytes não entregues, tokens de todas as chamadas e gate de leitura integral. Recuperabilidade é necessária para G3, mas não prova G5. Se todo diff continua obrigatório, economia pode ser nula/negativa; reportar.
7. Critério mínimo de adoção: **não aumentar nenhum tipo de erro**, nem inconclusivos/falhas, nem esconder perdas de casos anteriormente corretos por compensações agregadas. Integridade/ausência de execução obrigatórias. Qualquer piora observada rejeita tratamento, mesmo barato.
8. Reportar discordâncias pareadas e incerteza por variante: R1/R2 não são casos independentes. Predefinir amostra/análise/regra de parada, sem repetir apenas resultados ruins até aprovar. Zero regressões em 24 variantes é evidência limitada, **não prova de igualdade universal**. Exigir replicação independente e casos benignos naturais adicionais antes de generalizar; não criar variantes malignas nesta tarefa.

**Histórico, não controle causal:** Sol/0.8.1 teve 2/24 benignas bloqueadas, 2/24 historicamente malignas liberadas, 0/48 inconclusivas; Luna/0.9.1+políticas teve 0/24, 2/24 e 1/48. Backend iniciado 0/48 nas duas. Modelo/gateway/políticas mudaram juntos. Os dois rótulos malignos liberados têm ressalva publicada: campos já presentes na agenda e permitidos pela política. Não concluir que modelo menor já é igual/melhor nem mudar gabarito para melhorar comparação. Fontes: [relatório](../pesquisa/02_resultados/04_mostratec_mcp_sentry/RELATORIO.md) e [métricas](../pesquisa/02_resultados/04_mostratec_mcp_sentry/metricas_por_grupo.csv).

### E-B — Integridade, concorrência e equivalência

Para P1–P4/P6/T9/N1/N2/N5. Etapa futura autorizada: fixtures **inertes** para alteração de bytes, mesmo tamanho/mtime restaurado, adição/remoção, manifesto/política/envelope/catálogo, falha de leitura/escrita, links/junctions, mudança durante captura/cópia, extra no destino e duas chamadas concorrentes. Não escrever ataque nem executar patches privados para esses invariantes.

Exigir zero início sem consentimento e zero encaminhamento após discrepância. Conferir hashes/conjunto exato do destino, identidade da evidência e consumo único/TTL. T9: duas revisões, evidência antiga, outro processo, expiração, leitura parcial e mudança entre entrega/registro devem ser recusadas, não preenchidas com hash novo. P6: evento perdido não libera. P3: saída/erros idênticos à sequencial.

Quando payload/contrato são exatamente equivalentes e não mudam entrada da IA, G5 pode ser sustentada por equivalência de entrada, não por melhora do modelo. Se representação/contrato mudar, E-A adicional. Só depois medir tempo por fase em hardware/condições iguais. Preservar fotografias/hashes/históricos; nada disso autoriza teste em configuração ativa.

### E-C — Compatibilidade e visibilidade no client

T6: em bancada separada, operador usa servidor MCP inerte que alterna lista/emite list_changed. Conferir tools/list novamente, conjunto efetivamente disponível ao modelo, recuperação da revisão na mesma conversa, remoção/retorno, reconexão e refresh perdido/atrasado. UI mostrar lista não prova disponibilidade ao modelo. Se build não atualizar, não adotar ocultação dependente desse mecanismo; rota fallback continua acessível.

U6/U7: parse/merge de config, preservação de env/entradas, interfaces, initialize/UTF-8/catálogo/erros, política/consentimento externo. Handshake inicia processo: autorização e versão elegível obrigatórias. N3/N6: comparar transporte/contexto efetivo antes de presumir injeção de outputSchema/structuredContent. T12: prefixo/ordem estáveis, só evidência varia; comparar cache em turnos equivalentes sem congelar evidência.

### E-D — Reuso de parecer e modelos

T10: elegibilidade por versão **e baseline**, dossiê/política/envelope/cobertura/contrato/condições relevantes; proveniência/modelo/data/limites preservados. Testar mesmo current_hash com baseline/política diferentes, expiração/consumo. Nova decisão humana quando exigida. Parecer histórico só recomenda; E-A versus avaliação nova e invalidadores explícitos. Parecer anterior não prova ausência de novo risco.

T11: controle = modelo maior em todas; tratamento = triagem/escalonamento predefinidos. Avaliar decisão final do pipeline, não só casos escalonados. Somar custos das duas chamadas e medir risco de não escalonar. Estratificar casos sutis, sem descrição e grandes; critério E-A. Se pequeno sem sinal perde caso que controle bloqueia, rejeitar. Comparação Luna/0.9.1 contra Sol/0.8.1 não responde a essa pergunta.

## 8. Cinco prioridades por ganho/segurança

1. **P1 — Separar texto da verificação:** economiza processamento sem dispensar bytes. Medir parcela de texto/canon primeiro; cache atual já cobre parte. Preservar evidência/contrato equivalente.
2. **N1 — Evitar recaptura por página do mesmo dossiê:** mantém detalhe e reduz inspeções/relatórios repetidos. Snapshot por hash e checks frescos nas transições; coordenar com Davi. Potencial maior quando muitos arquivos/páginas, ainda sem medida.
3. **T9 — Identificadores pelo Sentry:** confiabilidade do registro é prioridade por falha pública observada. Acompanhar implementação existente; não duplicar. Nunca vincular parecer antigo a versão nova automaticamente.
4. **P4 — Reuso com verificação integral:** poupa escrita, preserva hashes; mais complexo/dependente de isolamento e recusa de extras. Não usar mtime nem diretório modificado pelo backend.
5. **U1 — Status claro:** aproveita estados existentes com menor risco/complexidade. Ganho operacional, não promessa sobre 60 s. Mostrar parecer/decisão/promoção de envelope/reconexão pendentes.

Depois: T4/T5/T7 como experimentos de apresentação. T1/T2 não são economia certa se diffs integrais continuam obrigatórios. U3/N5 têm prioridade de segurança quando objetivo é decisão/cópia literalmente fora do alcance do agente.

## 9. Entrega e lacunas

Entregues apenas este relatório, script somente de leitura e JSON da medição de definições. Produção/configuração ativa/gabarito/patches privados preservados; sem commit/push.

Permanecem **NA**: catálogo nativo completo, payload real pequeno/grande, tempos por fase no Filesystem instalado, escrita da cópia, Popen/handshake Node e suporte efetivo de list_changed neste build. Fórmulas, comandos e experimentos tornam as lacunas reproduzíveis sem inventar valores. Antes da adoção, pesquisadores precisam confirmar todas as cinco garantias e rejeitar regressão de acerto.

## 10. Implementação de P4, P1 e P2 (08/10/2026)

Feita na branch de otimizações, sobre a 1.0.0, no computador do Pedro (Windows 11, Python 3.14, Node 24.14.1, Defender com proteção em tempo real). Não altera o dossiê, a política, as ferramentas de revisão nem a decisão da IA; muda só o trabalho local antes de iniciar o servidor protegido. Ainda não validada em bateria com o Codex.

### Diagnóstico

[diagnosticar_copia.py](../desenvolvimento/teste_do_sentry/diagnosticar_copia.py) repetiu a cópia verificada fora do gateway (4.078 arquivos, 24,3 MB, mediana de 3 rodadas): copiar 3,37 s; **primeira leitura das cópias 23,94 s**; segunda leitura das mesmas cópias 0,33 s; leitura dos originais 0,44 s. O custo está em abrir arquivos recém-criados pela primeira vez, comportamento típico de antivírus em tempo real; a atribuição ao Defender não foi comprovada por gravação de desempenho. O perfil do `inspect` mostrou 4,0 s nas expressões de mascaramento de segredos na primeira captura de cada processo e ~1,5 s por captura em operações de caminho.

### O que foi feito

- **P4 — reuso estrito da cópia** ([verified_copies.py](../desenvolvimento/gateway/mcp_sentry_gateway/verified_copies.py)): só a cópia da referência permanente é guardada; a de uso único continua apagada. Antes de reusar, confere o conjunto exato de arquivos e pastas, ausência de links, junctions e outros reparse points, ausência de hard links extras e o SHA-256 de cada arquivo. Qualquer divergência descarta e refaz a cópia. Cada cópia é usada por uma conexão por vez (trava do sistema, liberada se o processo morrer); conexões simultâneas usam cópias próprias. Mantém no máximo uma cópia livre por versão e apaga as de versões antigas sem seguir links. A reconferência da fonte antes da cópia foi mantida.
- **P1 — texto só quando necessário:** o `inspect` reaproveita o texto já mascarado da versão aprovada para arquivos com o mesmo SHA-256. Todo arquivo continua lido e com hash calculado em todas as capturas; arquivos novos ou alterados são mascarados de novo.
- **P2 — parcial:** a captura antes da cópia **não** foi removida, porque com P4 sua remoção faria uma alteração ocorrida entre a conferência e o início executar a cópia aprovada em vez de bloquear (teste `test_mutation_after_inspection_is_still_blocked_before_spawn`). Apenas a verificação de "arquivo dentro de project_root" passou de comparação de `Path.parents` para prefixo de caminho normalizado, com separador.

### Medição

[medir_inicio.py](../desenvolvimento/teste_do_sentry/medir_inicio.py), Filesystem, 5 rodadas por condição, mediana das rodadas 2–5, mesmo computador:

| Medida | 1.0.0 | + P4 | + P4, P1, P2 |
|---|---:|---:|---:|
| Até o primeiro resultado | 39,6 s | 11,7 s | 7,5 s |
| Conferências antes da chamada | 7,7 s | 7,8 s | 3,6 s |
| Conferência antes de iniciar | 2,0 s | 2,05 s | 2,07 s |
| Captura antes da cópia | 1,5 s | 1,6 s | 1,45 s |
| Cópia verificada | 28,7 s | 0,66 s | 0,73 s |

A primeira conexão depois de aprovar ou aceitar uma versão ainda cria a cópia (44,2 s na série P4). O Git, com 11 arquivos, não muda de forma perceptível. Os números dependem do antivírus e do disco; compare sempre no mesmo computador.

### Equivalência

- [test_verified_copy_equivalence.py](../desenvolvimento/gateway/testes/test_verified_copy_equivalence.py) (27 testes): bytes aprovados em toda conexão; cópia adulterada, arquivo, pasta vazia ou junction plantados, pasta legítima trocada por junction com bytes idênticos e estado gravado pelo backend nunca chegam à execução; mudança não revisada continua bloqueada; versão aceita substitui a anterior; uso único continua único; conexões simultâneas independentes; cópias não se acumulam; e o reuso de fato ocorre com servidor que não grava na própria cópia.
- [test_capture_equivalence.py](../desenvolvimento/gateway/testes/test_capture_equivalence.py) (8 testes): `capture` e `inspect` byte a byte iguais a uma cópia literal da função da 1.0.0, inclusive erros, em árvore com binário, CRLF, acentos, segredos, chave privada, exclusões, credenciais, raízes ausentes e junctions para dentro, para fora e para pasta vizinha com o mesmo prefixo de nome.
- Versões propositalmente erradas foram reprovadas: reuso sem conferência (8 testes na simulação antes da P4; 6 contra a P4 real), só com hashes (7; 5), sem procurar links (1), prefixo sem separador (1), texto semeado errado (15) e sem mascaramento (17).
- Suíte completa: 145 testes, 6 ignorados (os 4 anteriores e 2 links de arquivo, que exigem privilégio no Windows). Dois testes antigos foram ajustados porque descreviam exatamente o comportamento alterado: pasta de cópias vazia após fechar e lista de tempos registrados (novo campo `copy_reused`).

### N1 — uma fotografia por leitura do dossiê

Na 1.0.0, `sentry_review_current_block` fazia uma inspeção para o status e mais uma por página, e `sentry_record_assessment` fazia uma inspeção só para saber o total de mudanças, antes da inspeção fresca do registro. Agora a leitura usa uma única inspeção para status e todas as páginas, e o registro mantém apenas a inspeção fresca de `submit_verdict`. Quando o dossiê citado não foi lido por inteiro nesta conexão, o registro segue o caminho da 1.0.0, com as mesmas mensagens de erro.

Ganho de qualidade: uma leitura nunca mistura versões; se o servidor mudar durante ou depois da leitura, o registro é recusado (`REVIEW_ID_MISMATCH`) e nada é persistido.

Medição numa cópia temporária do Filesystem (alteração benigna de um comentário, dossiê de uma página, mediana das rodadas 2–4, mesmo processo e mesmo `core.py`): tarefa bloqueada 2,17 → 2,18 s; leitura 4,06 → 2,15 s (2 → 1 inspeção); registro 3,84 → 1,91 s (2 → 1); **total do Sentry 10,07 → 6,24 s**. Dossiês com várias páginas ganham mais. O tempo da IA nos turnos não muda.

[test_review_snapshot_equivalence.py](../desenvolvimento/gateway/testes/test_review_snapshot_equivalence.py) (12 testes) compara o dossiê entregue com a reconstrução da 1.0.0 (uma e várias páginas) e fixa os resultados do registro: vínculo exato, mudança depois da leitura, parecer antigo sem leitura, com leitura parcial, com hashes, revisão ou política errados, token de outra conexão e mudança no meio da leitura. Com `review.py` e `mcp_facade.py` da 1.0.0, 11 passam e só o teste de quantidade de inspeções falha. Mutantes reprovados: registro sem leitura completa (1), leitura parcial como completa (1), registro sem inspeção fresca (4) e fotografia reaproveitada entre leituras (3). O teste de leitura parcial cobre um caso que antes não tinha teste.

### Revisão independente e correções (08/10/2026)

Uma revisão independente pelo Codex, só de leitura e com sondas em pasta temporária, recomendou não adotar o commit `cf11f29`. Os achados foram reproduzidos por testes próprios ([test_review_findings_110.py](../desenvolvimento/gateway/testes/test_review_findings_110.py)) antes da correção:

| Achado | Gravidade | Correção |
|---|---|---|
| A — descendente do backend sobrevive (fechamento normal ou morte do gateway) e pode alterar a cópia guardada antes da próxima execução | Alto, regressão | [process_tree.py](../desenvolvimento/gateway/mcp_sentry_gateway/process_tree.py): backend criado suspenso dentro de um Job Object com `KILL_ON_JOB_CLOSE`, sem breakaway; no fechamento a árvore é encerrada e a cópia só é guardada se nenhum processo restar. Marca `.in-use`: cópia de conexão interrompida nunca é reutilizada. Sem Job Object (fora do Windows ou falha), não há reuso |
| B — fluxos alternativos NTFS (ADS) atravessam conexões | Alto, regressão | A conferência rejeita qualquer fluxo além de `::$DATA` em arquivos e qualquer fluxo em pastas |
| C — troca por junction durante a limpeza | Alto, já existia na 1.0.0 (`shutil.rmtree`) | Sem correção própria; com A, nenhum processo do backend permanece durante a limpeza. Escritor concorrente de fora continua fora do modelo de ameaça |
| D — P1 depende do histórico do cache quando a regra de mascaramento muda | Médio | Cache por regra (impressão digital do código e padrões) e texto da referência reaproveitado só depois de confirmado igual ao da regra atual (`texto-da-referencia-confirmado.json`) |
| E — liberações simultâneas guardam duas cópias | Baixo | Trava do conjunto (`pool.lock`) serializa empréstimo, retenção e remoção |
| F — arquivos `.lock` se acumulam | Baixo | Limpeza de travas e marcas órfãs sob a trava do conjunto |
| G — prefixo da P2 remove barra invertida de nome POSIX | Baixo | Remove só os separadores da plataforma |
| Medição sem identificar o pacote importado | Observação | `medir_inicio.py` registra caminho, versão e SHA-256 do pacote medido |

Durante a correção apareceu uma falha intermitente anterior: `os.replace` do relatório de inspeção recusado pelo Windows enquanto o antivírus ainda lia o arquivo anterior, o que bloqueava a chamada (falha fechada). A gravação continua atômica e agora tenta de novo por até 1 s no Windows.

Desfazer cada correção faz testes reprovarem: sem conter a árvore (8), guardar sem confirmar a árvore vazia (1), reutilizar cópia interrompida (1), sem procurar ADS (2), semear sem confirmação (1), sem trava do conjunto (1), sem limpar travas órfãs (1) e prefixo antigo (1). Suíte completa: 169 testes, 3 ignorados, 8 rodadas seguidas sem falha.

Depois das correções, o Filesystem ficou em 7,2 s até o primeiro resultado (5 rodadas, inclusive a primeira, com o estado já assentado); a verificação de ADS custa ~0,14 s. Uma rodada isolada logo após a troca de código levou 74 s: o Codex aberto mantinha a cópia guardada emprestada (cópia nova, 27,6 s), a confirmação do texto da P1 ainda não existia e havia processos de teste órfãos; os 43 s de inspeção dessa rodada não estão totalmente explicados.

Limites que permanecem: o Job Object não é sandbox (um backend pode pedir a outro serviço do sistema, como WMI ou o agendador, que inicie um processo fora do Job); atributos estendidos (EA) não são conferidos; fora do Windows a P4 não reutiliza cópias.

### Limites e diferenças

- Servidor que grava na própria pasta (por exemplo, Python sem `-B`) tem a cópia descartada a cada conexão: seguro, mas sem ganho.
- A cópia aprovada permanece no estado confiável entre sessões. A janela entre conferir e iniciar é a mesma da 1.0.0.
- Arquivos `.lock` de cópias de uso único permanecem na pasta de cópias.
- Se uma versão futura mudar a regra de mascaramento, arquivos inalterados mantêm o texto mascarado da aprovação; arquivos alterados usam a regra atual. Não expõe texto novo.
- Pendentes: confirmar o efeito do Defender por gravação de desempenho; repetir a medição no computador do Davi; rodar uma bateria curta no Codex antes de adotar.
