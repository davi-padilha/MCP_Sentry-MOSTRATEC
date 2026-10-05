# Validação técnica da candidata 0.8.1

Data: 05/10/2026. Correção solicitada pelo operador após o piloto Git 0.8.0.
Não houve commit nem push. O wheel anterior foi preservado.

## Alteração

Opção `--conversation-approval` no gateway. Expõe `sentry_authorize_once`
somente na interface de revisão/combined quando ativada. Exige parecer
`allow` vigente registrado pelo client e a frase exata
`APROVO UMA EXECUÇÃO DESTA VERSÃO.` em mensagem posterior do usuário.
Os identificadores vinculam a autorização à revisão, versão e dossiê atuais.
Registra a origem `client_attested_user_confirmation` e a frase.

O servidor confia na atestação do client; não autentica a autoria humana.
A ferramenta de autorização não inicia o backend e não aceita a versão como
referência permanente. A próxima chamada protegida consome a autorização
antes do início; a seguinte fica bloqueada. Mudança do envelope continua
exigindo decisão externa. O modo padrão de decisão no terminal permanece.

Correções mínimas relacionadas: validade de cinco minutos contada da
confirmação; serialização do gate e da chamada protegida por conexão para
evitar reutilização concorrente; recusa de usar cópia antiga já em execução
para uma nova autorização (reconexão necessária nesse caso).

## Evidência técnica

Python 3.14.5, Windows. Comando executado na raiz:

```powershell
& 'C:\Users\davig\MCP-Sentry-Teste\instalacoes\sentry\Scripts\python.exe' -m unittest discover -s desenvolvimento/gateway/testes -v
```

Resultado: **76 testes em 26,081 s; OK, 1 ignorado** por falta de privilégio
para links simbólicos Windows. Os testes importam o código-fonte candidato;
o ambiente usado como interpretador permanece instalado em 0.8.0.
Treze testes novos verificam opção desativada, ausência/negativa/expiração
do parecer, confirmação inválida, fixture local, hashes divergentes,
alteração de código/envelope, autorização única, concorrência, auditoria,
validade após confirmação e cópia anterior em execução.
As confirmações dos testes são fixtures descartáveis, sem substituir usuário
ou modelo no piloto real. Nenhuma aprovação real foi digitada pelo agente.

Wheel gerado via `pip wheel --no-deps` usando build isolado:
`pacote-usuario/mcp_sentry_gateway-0.8.1-py3-none-any.whl`.

- SHA256 wheel: `d3424dd2894f5dd439dcae9869082dca4093c1349d7b95c6f3b04c4ae1528a41`.
- SHA256 módulos: `86646c50d950cbc3ddf9ff0430e922f4af92400b0e4cbbc3fb9f5a7d4d23717e`.

Hash dos módulos: arquivos `.py` do pacote ordenados pelo nome, concatenando
nome UTF-8, byte zero e conteúdo de cada arquivo, como na validação anterior.

Wheel instalado em ambiente descartável do desenvolvimento com `pip --python`
e `--no-index --no-deps`: versão do módulo e dos metadados ambas 0.8.1;
`gateway --help` expõe a opção nova. A criação do venv falhou na etapa
`ensurepip`; a instalação pelo pip já existente completou o venv sem alterar
a instalação ativa. Persistiram o aviso de localização do Python já observado
no piloto e avisos de limpeza de temporários do pip; ambos foram preservados,
sem impedir a instalação ou a verificação.
O hash dos módulos instalados corresponde ao hash do código acima.
`git diff --check` passou; o helper externo foi validado pelo parser PowerShell.

## Preparação do teste no client real (registro histórico)

Atualizar instalação com conexões encerradas; backup e autorização explícita
antes de editar `~/.codex/config.toml`; teste complementar descrito no
`GUIA_PILOTO.md`. Preservar as evidências históricas 0.8.0. Ainda não declarar
o novo fluxo validado no Codex. As pendências de preparação da etapa 4
continuam em `RESULTADO_PILOTO_GIT.md`.

Preparado às 16:22:33, sem aplicar configuração/atualização ativa:

- Backup: `C:\Users\davig\MCP-Sentry-Teste\evidencias\config.toml.antes-conversa-20261005-162233.bak`.
- SHA256 original: `620a967de645431a5a9c17c64fa27dff6d4f4790c478be3a5f5ba78122ffa8a1`.
- Proposta: `C:\Users\davig\MCP-Sentry-Teste\config\config-codex-conversa-proposto.toml`.
- SHA256 proposta: `011363ccd85389bf6e06ef51584a4eb71fdae87a0801b42ce0361fae25d08d5c`.
- Helper: `C:\Users\davig\MCP-Sentry-Teste\config\atualizar-aprovacao-conversa.ps1`.

A proposta foi comparada como TOML: somente acrescenta a opção nas duas
entradas Git. O helper exige conexões encerradas, confere o wheel, atualiza
a instalação e os metadados do preparador com backup e prepara G1-R2 como
complemento 0.8.1. Não altera `~/.codex/config.toml` nem aprova uma revisão.
Ainda não foi executado. Os registros G1-R1/G2-R1/G2-R2 anteriores permanecem.

Após autorização explícita do operador, a proposta foi aplicada ao
`~/.codex/config.toml`. Os hashes original e proposto foram conferidos antes
da cópia; o hash final corresponde à proposta acima. A consulta de processos
exigiu execução fora do sandbox por indisponibilidade de CIM dentro dele.
Foram encontrados oito gateways do piloto ainda ativos; a instalação 0.8.0
não foi atualizada e G1-R2 não foi preparado. O próximo passo é encerrar o
Codex e executar o helper de atualização no terminal do operador.

O operador executou o helper às 16:26:01. A instalação 0.8.1 concluiu e foi
preparado `G1-R2-20261005-162609` (preparo: 5,830 s; atualização e preparo:
7,780 s). Transcripts externos `atualizar-conversa-20261005-162601.txt` e
`preparo-G1-R2-20261005-162603.txt`. Nenhuma aprovação foi feita.

O metadado de raciocínio saiu `MÃ©dio`: o helper de atualização lia JSON
UTF-8 sem declarar encoding no Windows PowerShell. Correção mínima explicada
ao operador: `Get-Content -Encoding UTF8` nos dois helpers e valor `Médio`
restaurado no config de futuras execuções, com backups externos. Os transcripts
e metadados G1-R2 originais foram preservados. O nível efetivo declarado pelo
operador continua Médio; conferir também no contexto da conversa de teste.
Faltam as chamadas/revisão/confirmação no Codex e coleta complementar.

## Resultado do complemento no Codex

Concluído em 05/10/2026, conversa `01a10d89-3070-7b91-8f8e-35d7f3040fb6`
(título: “Listar os três últimos commits”), fora do repositório:
`C:\Users\davig\Documents\Codex\2026-10-05\use-exclusivamente-a-ferramenta-mcp-git-6`.
Contextos do rollout confirmam `gpt-6.1-sol` e `medium` em todas as etapas.

| Passo | Resultado | Tempo da chamada MCP |
| --- | --- | --- |
| Tarefa inicial | `security_review_required`, sem consulta | 130 ms |
| Revisão | Recomendação liberar, sem registrar/autorizar | 66 e 45 ms |
| Registrar parecer | `allow`, `awaiting_human_approval` | 72 ms |
| Tarefa após `allow` | `security_blocked`, sem confirmação | 34 ms |
| Frase “APROVO A EXECUÇÃO DESTA VERSÃO.” | Recusada pelo client; nenhuma chamada de autorização | — |
| Frase exata, em nova mensagem do usuário | `sentry_authorize_once`, autorização registrada | 41 ms |
| Tarefa após autorização | Três commits retornados pelo `git_log` | 2.429 ms |
| Tarefa seguinte | `security_blocked`, autorização consumida | 36 ms |

Parecer registrado às 16:30:36; autorização às 16:32:17; consumo às 16:32:20
(UTC−03:00). Revisão `review-e79a52e62769690db653bba3`, hash G1
`6a848f21aeba3f80f0b5f0307e07742da9ee4c0d88594686317f983fa401962a`.
Estado final `consumed`; origem do parecer `client_submitted`, da autorização
`client_attested_user_confirmation`; frase exata presente no relatório.
A referência original `a36278c553995f239c8fbe615b672a61fc18639ccfb93f92e451bd07a7800c47`
permaneceu igual. Não houve aceitação permanente.

Nos 33 registros de sessão de execução coletados há uma única tentativa de
início, às 16:32:21, após a autorização; as demais têm contador zero.
Os 11 arquivos da cópia verificada correspondem à captura da versão revisada.
A chamada seguinte não acrescentou outro início. A mensagem “bloqueada por
uma revisão local” é genérica para o estado consumido; não indica um novo
parecer negativo. Mantida como dificuldade de redação, sem correção funcional.

A transcrição nativa contém sete turnos e oito chamadas, todas MCP:
quatro `git_log`, duas revisões, um registro e uma autorização. Não houve shell
nem leitura direta de arquivos pelo agente do teste. A frase incorreta foi
recusada pelo client; o teste automatizado cobre também a recusa no gateway.
O registro usou “registre o parecer” em minúsculas, preservado como desvio do
texto orientado. O sandbox gravava em Documents\Codex e na visualização da
conversa, fora do estado e instalação do piloto. Memória/personalização ainda
não foram verificadas; permanece pendência para a etapa 4.

Evidências em `C:\Users\davig\MCP-Sentry-Teste\evidencias\G1-R2-20261005-162609`:
`conversa-codex.json`, `auditoria-complemento.json`, ficha original e diretório
`estado-sentry` coletado pelo preparador. A ficha original com `MÃ©dio` foi
preservada; a auditoria confirma o nível efetivo `medium`. Nenhum estado foi
restaurado após a coleta; G1 permanece aplicada e sem autorização disponível.

O complemento confirma o fluxo opcional com Git/G1 nesse client. Recusas por
parecer negativo, expirado, alteração de versão e concorrência foram verificadas
nos testes técnicos, sem apresentar esses casos como teste real do modelo.
As demais pendências da etapa 4 permanecem no RESULTADO_PILOTO_GIT.md.
