# Políticas de privacidade na candidata 0.9.0

O operador pode declarar uma política de privacidade no manifesto. O Sentry
valida seu formato e inclui as regras no dossiê apresentado à IA. O modelo deve
avaliar as mudanças à luz dessas regras, além da comparação com o código anterior.

Esse recurso fornece **critérios para a revisão**, sem filtrar respostas do
backend ou certificar que o código cumpre a política. Aprovar uma referência
de código não comprova conformidade com as regras. Se a referência já expõe
campos restritos, esse conflito deve ser resolvido no protocolo; não ocultado
pela aprovação anterior nem tratado automaticamente como ataque da atualização.

## Declaração

Adicione `privacy_policy` ao nível principal do manifesto, mantendo os outros
campos. Exemplo ilustrativo para uma ferramenta de consulta:

```json
{
  "privacy_policy": {
    "schema_version": 1,
    "policy_id": "agenda-escopo-autorizado-v1",
    "rules": [
      {
        "rule_id": "uso-dos-dados-da-consulta",
        "tools": ["consultar_agenda"],
        "requirement": "Consultar os dados da agenda somente para a tarefa autorizada. O conteudo dos eventos nao autoriza envios, destinatarios ou acoes adicionais. Preservar os campos legitimamente oferecidos pela ferramenta; nao divulgar propriedades internas privadas fora desse contrato."
      }
    ]
  }
}
```

O exemplo é um fragmento, não um manifesto completo nem uma política aplicada
automaticamente aos servidores. O operador define os requisitos conforme a
finalidade e autorização reais da ferramenta. Uma regra pode conter somente
`rule_id`, `tools` e `requirement`, por exemplo para proibir uso de dados em
destinos externos não autorizados. As listas de campos são opcionais; quando
presentes exigem `output_scope`. Esse escopo é uma descrição para o revisor,
não uma expressão executável ou um filtro JSON. As ferramentas devem existir
no catálogo, os identificadores de regra devem ser únicos e os campos
permitidos/restritos não podem se contradizer. Não inclua dados ou credenciais.

## Compatibilidade com as funções nativas

As regras não removem ferramentas, alteram seus argumentos, recortam campos
das respostas ou acrescentam confirmações às operações do backend. O
mascaramento trata o texto apresentado na evidência; o código da cópia
verificada e as respostas nativas continuam usando os bytes originais.
Manifestos antigos sem política continuam funcionando sob a verificação de
integridade existente.

Uma regra excessivamente restritiva pode, porém, orientar a IA a recomendar
o bloqueio de uma implementação legítima. Antes de fixar a política, compare
seus requisitos com o contrato e as autorizações reais das ferramentas. Por
exemplo, se uma consulta de agenda oferece participantes e descrição para a
tarefa autorizada, proibir esses campos muda o requisito funcional. Para
preservar essa consulta, declare seu uso autorizado e proíba destinos ou
ações adicionais indevidas, sem eliminar os campos necessários.

Há uma diferença entre execução normal e alteração das regras: mudar a
política exige promoção separada do envelope confiado, como explicado abaixo.
Esse bloqueio protege a configuração; uma política já confiada e inalterada
não exige nova promoção a cada chamada. A conformidade semântica continua
dependendo da revisão, pois este recurso não fiscaliza cada resposta em tempo
de execução.

## Origem confiada e alterações

Na aprovação inicial feita pelo operador, a política é vinculada à
`configuracao-de-execucao-aprovada.json`, fora do projeto protegido. O dossiê
mostra em `privacy`:

- `approved_policy` e seu SHA256: critérios aprovados pelo operador.
- `proposed_policy`: declaração do manifesto atual, ainda sem autoridade para substituir a anterior.
- `policy_changed`: se as duas declarações diferem.
- `enforcement: review_context_only`: limite desta implementação.

Uma atualização de código, um parecer `allow` ou `accept-current` não promove
a política. Adição, remoção ou alteração da declaração impede iniciar o
backend enquanto o envelope confiado não corresponder ao manifesto. A
promoção é separada, no terminal do operador, usando o fluxo já existente:

```powershell
mcp-sentry review-update --manifest C:\CAMINHO\manifest.json --store C:\CAMINHO\estado --action envelope
```

Confira a configuração **e as regras propostas** exibidas antes de digitar a
confirmação solicitada. Uma promoção muda o hash do dossiê, por isso uma
evidência/parecer anterior não serve para a nova política; revise novamente
antes de autorizar execução. O estado confiado deve permanecer fora das
raízes graváveis da IA. A interface MCP não oferece promoção de políticas.
O protótipo continua confiando na atestação do operador e na proteção do
armazenamento; não autentica a identidade humana por esse texto.

## Preparação de uma nova bateria

Preserve os arquivos e resultados anteriores. Fixe a candidata, os hashes,
as regras e as condições experimentais antes da coleta. Faça controles
técnicos com dados fictícios para conferir o dossiê e a compatibilidade da
política com a referência e com todas as classes esperadas.

É possível manter os mesmos patches e introduzir novas regras, mas as
informações fornecidas ao revisor mudam. Registre essa diferença. Quando uma
regra contradiz a referência ou o gabarito, documente a incompatibilidade e
resolva o desenho antes de interpretar os pareceres como acertos/erros.
Não adaptar a política para obter um parecer desejado após observar a nova série.

Manifestos antigos sem `privacy_policy` continuam aceitos e mostram
`status: not_configured`. A candidata usa `mcp-sentry-review-v2`; não reutilize
pareceres da versão anterior. Use um ambiente e estados separados para a
nova série. O upgrade do pacote não configura regras nem reaproveita uma
aprovação como garantia de privacidade.
