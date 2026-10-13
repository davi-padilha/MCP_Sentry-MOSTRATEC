# Fechamento da distribuição MCP Sentry 1.1.0

Validação concluída em **13/10/2026**, fuso America/Sao_Paulo. Escopo:
protótipo Windows para ferramentas MCP locais via `stdio`.

## Entrega

- Pasta: `instalar-mcp-sentry/`, onze arquivos, sem ambiente virtual ou estado:
  README e `INSTALAR.cmd` na raiz, cinco guias em `ajuda/` e quatro componentes
  em `arquivos-instalacao/`.
- ZIP: `distribuicoes/mcp-sentry-1.1.0.zip`.
- Wheel: `mcp_sentry_gateway-1.1.0-py3-none-any.whl`.
- SHA-256 do wheel: `42a1b327137b525e6f0848eca3eebaf2357cea127d9e0ed32f3a8d65320cb80d`.
- SHA-256 do ZIP: `eef146ac4a7bcc2b73954bab47da5fc4c76c843132153656a4f7c828233018ce`.
- Identidade dos 18 módulos da fonte empacotada:
  `9626c5aeb8b7ccf148d70f3d9396e99d7d63fb1af19b28f001ba52ec7a2c84e4`.

O código do pacote `mcp_sentry_gateway` e o `pyproject.toml` permanecem iguais
ao commit `518c705c004cfbf99f882fc288b35c60807549e0`, usado nas campanhas da
1.1.0 e incorporado à main por `980418c`. Esta entrega reconstrói o wheel;
seu hash é diferente do wheel experimental. As campanhas anteriores não foram
repetidas nem atribuídas ao novo hash. README e ferramentas de distribuição
receberam as melhorias descritas abaixo.

A 1.0.0 foi preservada em `distribuicoes-historicas/`, com o hash original
`90c4f944160c03fbf90e9f7b1fc4777a86c567b9c223a92c2d08ce38c7cc4b4f`.

## Melhorias implementadas

- Preparação automatizada: build em cópia isolada, validação, somas e ZIP.
  Uma candidata com falha de validação não substitui a entrega.
- O preparador lê a versão do pyproject e confere `__version__`; o instalador
  usa a identificação gerada, sem fixar o número da versão no PowerShell.
- O instalador confere todos os arquivos listados antes de executar Python.
  Textos da distribuição usam LF; o lançador CMD usa CRLF. Ambos são fixados
  em `.gitattributes` para preservar as somas após checkout.
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
- `INSTALAR.cmd` abre o instalador pelo Windows PowerShell, preserva o código
  de saída e deixa a mensagem visível. A política de execução é ajustada
  somente no processo, sem alterar a configuração global.
- Instalação nova em `%LOCALAPPDATA%\MCP-Sentry-Gateway\.venv`; os guias e
  identificação são copiados para `ajuda-mcp-sentry` junto ao ambiente.
  Remover a pasta extraída não remove o programa instalado.
- Uma `.venv` antiga na raiz da pasta de entrega é reutilizada no mesmo
  caminho. A distribuição não migra automaticamente conexões já configuradas.
- README inicial reduzido a três passos. Uso e atualização têm guia próprio;
  configuração manual e privacidade são referências separadas. Instruções de
  pesquisa foram retiradas do guia de privacidade entregue ao usuário.
- `VERSAO.json` contém seis campos de identificação; resultados e proveniência
  permanecem nos registros técnicos fora do ZIP.

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
| Lançador CMD | Instalou em caminho com espaços e devolveu falha para pacote alterado |
| Pasta fixa e ajuda instalada | Caminho padrão conferido em perfil descartável; cinco guias e identificação copiados |
| Pasta extraída retirada | Fluxo MCP completo passou após o caminho original desaparecer |
| Ambiente antigo na raiz da entrega | Atualização no mesmo caminho, sem migração automática |
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
`laboratorio/execucoes/distribuicao-1.1.0-nuu4cknp/validacao/`.
Contém suíte, instalação, upgrade, rejeições, setup, stdio, lançador, instalação
fixa e SDK, além de `validacao.json`. A área é ignorada pelo Git. A identificação
pública está em `instalar-mcp-sentry/arquivos-instalacao/VERSAO.json`; os resultados
completos não integram os arquivos apresentados ao usuário.

Duas candidatas anteriores não foram publicadas enquanto se corrigia o novo
validador: expectativa do estado após parecer e captura da mensagem de oferta
do PowerShell. O protocolo de bloqueio foi conferido contra a implementação;
o teste exige `action_executed: false` e ausência de início do backend.
Na reorganização da entrega, a candidata `9n1vc5il` não foi publicada porque
o validador escapava incorretamente os argumentos do CMD. A chamada do teste
foi corrigida; a execução final conferiu sucesso e falha do lançador real.

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

## Organização das pastas de entrega

A pasta histórica foi renomeada para `distribuicoes-historicas/`. Seus sete
wheels foram conferidos byte a byte contra os arquivos anteriores. O guia
antigo foi preservado como `GUIA_LEGADO.md`, com um índice próprio no README.
Os scripts de preparação, atualização e reprodução usam o novo caminho.
Manuais atuais apontam para `instalar-mcp-sentry/`.

O wheel e o ZIP foram reconstruídos para corrigir também a descrição de
pastas incluída nos metadados do pacote. A execução final acima passou
novamente pelos controles de instalação, atualização, stdio e SDK; os
18 módulos do gateway continuam inalterados.

## Reorganização e ambiente de desenvolvimento

A bateria portátil fica em `reproducao-experimentos/sentry-1.0/` e conserva
todos os hashes esperados. Quatro textos foram restaurados de CRLF para os
bytes LF originais; o manifesto não foi alterado. A nova regra de atributos
fica fora do pacote congelado. As ferramentas de avaliação ficam em
`desenvolvimento/avaliacao-sentry/`. Estes registros de validação foram
agrupados em `documentacao/validacoes/`, com os links atualizados.

O ambiente `desenvolvimento/gateway/.venv` foi atualizado da 0.8.0 para
a 1.1.0 usando o wheel local. A entrega foi reconstruída e validada novamente
para acompanhar a descrição de pastas nos metadados. Os logs, resultados e
snapshots das cinco execuções locais foram preservados; suas pastas `.venv`
geradas foram removidas após o término dos processos. A limpeza está
registrada em `laboratorio/execucoes/LIMPEZA_AMBIENTES.json`.

Após validar a organização final do ZIP, os doze ambientes temporários das
candidatas `9n1vc5il` e `nuu4cknp` foram removidos. Logs, resultados, referências
fictícias e cópias de ajuda permanecem disponíveis. Registro:
`laboratorio/execucoes/LIMPEZA_AMBIENTES_DISTRIBUICAO_FINAL.json`.
