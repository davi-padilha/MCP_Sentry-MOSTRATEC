# Desenvolvimento do gateway atual

Código-fonte da versão 1.3.1 do protótipo. O usuário recebe a pasta
[instalar-mcp-sentry/](../../instalar-mcp-sentry/README.md), com o wheel e seu manual;
O ZIP fica em `distribuicoes/`; as entregas anteriores permanecem preservadas.
O protótipo antigo está em [prototipo-feicit/](../../prototipo-feicit/README.md).

A 1.3.1 torna explícita a oferta de revisão somente leitura na resposta do
bloqueio e nas instruções da interface de execução. O cliente deve oferecer
revisar pelo conector separado, a pedido do usuário, sem registrar parecer
ou aprovar a versão. A oferta inclui a frase curta “Faça a revisão sugerida.”.
Essa orientação não comprova que um modelo a seguirá; o novo teste real é separado.

A 1.3.0 acrescenta `sentry_accept_version` no modo opt-in de aprovação pelo
chat. Depois de allow registrado, o cliente oferece aceitação permanente ou
uma chamada e pede confirmação própria para a opção escolhida. A aceitação
reconfere vínculos e atualiza atomicamente a baseline após persistir evidências
obrigatórias; configuração, cobertura, política e catálogo não são promovidos.
Uso repetido e reconexão continuam permitidos enquanto o código for igual,
e alterações posteriores bloqueiam novamente. Uma cópia antiga em execução
é encerrada e substituída pela cópia da referência aceita antes da próxima
chamada. O assistente/preparador aceita `--conversation-approval`; o padrão
externo permanece compatível. A atestação do cliente não autentica o usuário.

A 1.2.0 acrescenta configuração assistida para Claude Desktop: `setup --client
claude-desktop`, detecção dos perfis Windows/Store, fragmento JSON, diagnóstico,
inventário e restauração seletiva com backup e rejeição de conflitos. Execução
e revisão usam o mesmo manifesto/estado e processos separados; credenciais são
mantidas somente na execução. A preparação e os controles de integridade são
compartilhados com o Codex. Claude Code será uma etapa posterior. Os testes
técnicos não validam o comportamento de um modelo Claude real.

A 1.1.0 reduz o tempo local sem mudar o que a IA recebe: reuso estrito da cópia
verificada (P4), texto mascarado reaproveitado para bytes idênticos (P1),
reconferência mais barata antes da cópia (P2 parcial) e uma inspeção por
leitura do dossiê (N1). Testes de equivalência e medições estão na seção 10 de
[ANALISE_OTIMIZACOES.md](../../documentacao/ANALISE_OTIMIZACOES.md).

A 1.0.0 distingue erros de campos ausentes e formatos misturados, com instruções
de recuperação e rejeição de vínculos inválidos. O diff contém 12 linhas de
contexto, hashes dos arquivos alterados e limites explícitos da comparação.
As orientações do dossiê entram em sua identidade; não certificam privacidade
nem escolhem automaticamente a decisão. As ferramentas nativas são preservadas.
As distribuições anteriores ficam em `distribuicoes-historicas/` para reprodução.

A 0.10.0 acrescenta `review_binding` às evidências, erros com código e
interface de releitura, recibo do parecer efetivamente persistido e contrato
de privacidade declarado pelo operador. As medições locais por etapa ficam
fora dos hashes e não alteram as respostas nativas. A telemetria é auxiliar;
falhas nos registros obrigatórios continuam impedindo a transição de decisão.
Os campos antigos de entrada do parecer permanecem compatíveis. Copie os
quatro campos de `review_binding` para o parecer sem alterar seus valores.

A 0.11.0 oferece registro por `review_token`, emitido somente apos leitura
completa na mesma conexao e vinculado ao dossie lido. Envie `review_token`,
`decision`, `justification` e `risks`, ou use o formato anterior `verdict`.
Tokens inventados, de outra conexao, expirados ou ligados a outra atualizacao
continuam rejeitados. Os erros orientam releitura e reenvio.

A CLI `status` consulta todas as conexoes protegidas sem escrever no estado.
`restore-codex --installation-record CAMINHO` apresenta uma restauracao seletiva;
`--apply` aplica com backup e rejeicao de conflitos. O setup novo guarda
`codex-installation.json`; instalacoes antigas sem esse registro exigem
conferencia manual do backup. Estado, credenciais e pacotes nao sao removidos.

As medidas de inicializacao separam verificacao anterior ao processo, captura
da origem, copia verificada, criacao do processo, negociacao MCP e catalogo.
`startup_total` contem essas etapas; nao some novamente ao tempo do turno.
Nenhum cache de integridade foi introduzido.

Na 0.9.0, o mascaramento distingue chaves secretas de literais como
`"password="`, preserva linhas físicas e evita deformar o diff. A política
opcional de privacidade fornece critérios confiados pelo operador para a
revisão. Ela não filtra respostas em execução. Configuração, promoção e
limites estão em [PRIVACIDADE.md](../../instalar-mcp-sentry/ajuda/PRIVACIDADE.md).

A 0.9.1 sincroniza o esquema de registro do parecer com o protocolo v2,
eliminando a incompatibilidade de versão anunciada na 0.9.0. Evidências em
[VALIDACAO_0.9.1.md](../../documentacao/validacoes/VALIDACAO_0.9.1.md).

Na raiz do repositório, em PowerShell:

```powershell
python -m venv .\desenvolvimento\gateway\.venv
& .\desenvolvimento\gateway\.venv\Scripts\python.exe -m pip install .\desenvolvimento\gateway
& .\desenvolvimento\gateway\.venv\Scripts\python.exe -m unittest discover -s desenvolvimento/gateway/testes -q
```

Para gerar uma distribuição nova, use o comando de preparação e validação
em [desenvolvimento/distribuicao/](../distribuicao/README.md). A versão é lida do
pyproject.toml e conferida contra o pacote. Ambientes virtuais, testes e
arquivos intermediários não fazem parte da entrega ao usuário.

[Validação da entrega atual 1.3.1](../../documentacao/validacoes/VALIDACAO_1.3.1.md).

[Validacao da 0.11.0](../../documentacao/validacoes/VALIDACAO_0.11.0.md).

[Guia do piloto](../../documentacao/GUIA_PILOTO.md).
