# Fechamento da distribuição MCP Sentry 1.1.0

Validação concluída em **13/10/2026**, fuso America/Sao_Paulo. Escopo:
protótipo Windows para ferramentas MCP locais via `stdio`.

## Entrega

- Pasta: `instalar-mcp-sentry/`, oito arquivos, sem ambiente virtual ou estado.
- ZIP: `distribuicoes/mcp-sentry-1.1.0.zip`.
- Wheel: `mcp_sentry_gateway-1.1.0-py3-none-any.whl`.
- SHA-256 do wheel: `61f8e51bb0761a196c72946da8fcbf11416e185c14d6500821443a85d28ebdad`.
- SHA-256 do ZIP: `bcbca81314955e8fb702706462c9ec5135859058566ab9efdecfea9ade028f62`.
- Identidade dos 18 módulos da fonte empacotada:
  `9626c5aeb8b7ccf148d70f3d9396e99d7d63fb1af19b28f001ba52ec7a2c84e4`.

O código do pacote `mcp_sentry_gateway` e o `pyproject.toml` permanecem iguais
ao commit `518c705c004cfbf99f882fc288b35c60807549e0`, usado nas campanhas da
1.1.0 e incorporado à main por `980418c`. Esta entrega reconstrói o wheel;
seu hash é diferente do wheel experimental. As campanhas anteriores não foram
repetidas nem atribuídas ao novo hash. README e ferramentas de distribuição
receberam as melhorias descritas abaixo.

A 1.0.0 foi preservada em `pacote-usuario/`, com o hash original
`90c4f944160c03fbf90e9f7b1fc4777a86c567b9c223a92c2d08ce38c7cc4b4f`.

## Melhorias implementadas

- Preparação automatizada: build em cópia isolada, validação, somas e ZIP.
  Uma candidata com falha de validação não substitui a entrega.
- O preparador lê a versão do pyproject e confere `__version__`; o instalador
  usa a identificação gerada, sem fixar o número da versão no PowerShell.
- O instalador confere todos os arquivos listados antes de executar Python.
  Textos da distribuição usam LF, fixado também em `.gitattributes`.
- Procura Python por launcher, PATH, diretórios usuais e registro. Executáveis
  são sondados; aliases inválidos não são aceitos como uma instalação.
- Confere versão mínima, `venv` e `ensurepip` antes de criar o ambiente.
- Oferece setup em instalação nova. `-Configurar` abre o assistente e
  `-SemConfigurar` permite instalação sem perguntas. Confirmar descoberta,
  referência e substituição de configuração continua sendo ação do operador.
- `-Ambiente` permite atualizar a instalação anterior sem mudar seus caminhos
  ou repetir setup. Ambientes incompletos não são sobrescritos; um venv válido
  sem o pacote pode ser usado para retomar uma instalação interrompida.
- O resumo distingue programa instalado de MCP conectado e mostra caminhos
  e próximo comando. Os guias foram atualizados, inclusive um exemplo JSON
  cujo caminho tinha escape incorreto.

## Controles executados

| Controle | Resultado |
| --- | --- |
| Suíte do gateway em CPython 3.12.14 | 180 testes; 177 passaram e 3 ignorados por privilégio de symlink no Windows |
| Fonte, wheel e instalação | 18 módulos com bytes iguais e inventário completo |
| PowerShell 5.1: instalação limpa | Passou, inclusive pasta com espaços |
| Atualização 1.0.0 → 1.1.0 | Passou, preservando hashes da referência/configuração fictícias e caminho do ambiente |
| Detecção automática de Python | Encontrou CPython 3.14.5 apesar dos aliases inválidos disponíveis no PATH |
| Arquivo de entrega alterado | Rejeitado antes de criar ambiente |
| Executável Python inexistente | Rejeitado com orientação, antes de criar ambiente |
| Pasta de ambiente incompleta | Conteúdo preservado, instalação recusada |
| Venv válido sem pacote | Instalação concluída no ambiente existente |
| Oferta de configuração | Recusa respeitada; nenhum setup iniciado |
| Setup solicitado | Conectou MCP fictício com confirmações; backup e registro de instalação conferidos |
| MCP por stdio | Resposta nativa preservada e alteração bloqueada antes do início |
| Revisão independente | Executor não ofereceu ferramentas administrativas; revisor não ofereceu o backend |
| Registro do parecer | Campo ausente recuperável; recibo corresponde ao persistido; parecer não autorizou execução |
| Autorização do operador | Um início autorizado retomou a tarefa; conexão posterior voltou a bloquear |
| SDK MCP oficial, em CPython 3.14.5 | Schema e chamadas válidos: 1 ferramenta no executor e 4 no revisor |

O servidor fictício cria um marcador ao iniciar. Os controles de bloqueio
conferiram a ausência desse marcador antes da autorização, durante revisão e
depois do consumo do início autorizado. Não foram usados servidores reais,
contas, dados pessoais, modelo de IA ou chamadas externas.

## Reprodução e evidências

Consulte `desenvolvimento/distribuicao/README.md`. O comando usado foi:

```powershell
& 'CAMINHO_DO_PYTHON_3.12\python.exe' -B desenvolvimento/distribuicao/preparar_distribuicao.py --python-sdk 'CAMINHO_DO_PYTHON_COM_SDK\python.exe'
```

Evidências finais locais:
`laboratorio/execucoes/distribuicao-1.1.0-r8z486bu/validacao/`.
Contém suíte, instalação, upgrade, rejeições, setup, stdio, SDK e
`validacao.json`. A área é ignorada pelo Git. O resumo público e a identificação
estão em `instalar-mcp-sentry/VERSAO.json`.

Duas candidatas anteriores não foram publicadas enquanto se corrigia o novo
validador: expectativa do estado após parecer e captura da mensagem de oferta
do PowerShell. O protocolo de bloqueio foi conferido contra a implementação;
o teste exige `action_executed: false` e ausência de início do backend.

## Limites

O requisito declarado continua Python 3.11+, mas esta entrega não certifica
todas as versões ou sistemas operacionais. A suíte/instalação principal usou
3.12.14; detecção e instalação automáticas usaram 3.14.5, e o SDK nesse runtime
conectou ao gateway instalado no ambiente principal. Não houve novo piloto no
Claude ou nova bateria de modelo.

Todos os estados e arquivos de configuração usados são descartáveis. A
configuração ativa dos clientes não foi consultada nem modificada pelos novos
validadores. A proteção do estado contra outros processos do mesmo usuário
continua sendo condição confiada; estes testes não demonstram isolamento por
ACL, sandbox nem autenticação humana.
