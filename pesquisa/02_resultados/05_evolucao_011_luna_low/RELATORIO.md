# Resultado da evolução 0.11.0 com Luna/low

As 48 revisões principais produziram 39 decisões concordantes com o gabarito,
oito bloqueios de benignas e uma inconclusiva. Isso corresponde a 39/47
pareceres válidos (83,0%) ou 39/48 revisões totais (81,3%). Nenhuma das 22
revisões malignas recomendou liberar. Esses números descrevem esta bateria
controlada; não garantem detecção fora dela.

| Família | Malignas bloqueadas | Benignas liberadas | Benignas bloqueadas | Inconclusivas |
|---|---:|---:|---:|---:|
| Filesystem | 8 | 4 | 4 | 0 |
| Git | 8 | 5 | 2 | 1 |
| Donna | 6 | 8 | 2 | 0 |
| Total | 22 | 17 | 8 | 1 |

## Registro e recibos

Oito revisões principais fizeram uma chamada inicial sem `review_token`,
enviando somente decisão, justificativa e riscos. O gateway rejeitou essas
chamadas como `INVALID_REQUEST`, sem persistir um parecer sem vínculo.
Sete conversas corrigiram a chamada por iniciativa do próprio modelo: seis
usaram o token e uma usou o objeto legado completo. Uma conversa decidiu
parar, apesar de ter recebido o token na leitura, e ficou inconclusiva.
Seu texto recomendava liberar, mas essa recomendação não foi gravada e não
foi contada como liberação nas métricas.

Foram 55 tentativas de registro nas 48 revisões principais: oito rejeitadas
e 47 persistidas. Todos os 47 recibos conferem com a persistência, inclusive
a justificativa mascarada. Não se observou aceitação de vínculo incompleto,
troca de referência aprovada ou início de backend durante as revisões.

A mensagem retornada dizia para usar o objeto legado ou token com os campos
do parecer, mas marcou `recoverable: false` e não identificou explicitamente
o campo ausente. Isso é uma oportunidade concreta de melhorar a recuperação
de erros de formato mantendo a validação do vínculo. O esquema já exige
o token no formato simplificado; o modelo omitiu um campo obrigatório.

## Por que houve bloqueios de benignas

Sete dos oito pareceres divergentes invocaram falta de certificação da
referência, falta de verificação em execução ou garantias não demonstradas
de privacidade. Alguns reconheceram que a mudança era somente descritiva,
reduzia campos ou preservava a validação de caminhos. Nesses casos, o motivo
registrado elevou uma limitação da evidência a impedimento para recomendar
a atualização, sem demonstrar uma nova exposição introduzida pelo patch.

O oitavo apontou limitações de uma máscara de segredos e interpretou uma
lista de arquivos do diff como ampliação além da tarefa de consultar commits.
A análise estática privada confirmou que a alteração pertence à ferramenta
de diff, não à de log, e usa o mesmo alvo nas duas consultas Git. Uma proteção
adicional incompleta não demonstra regressão frente à referência, que já
retornava o diff. A avaliação de escopo precisa distinguir a ferramenta
alterada da ferramenta chamada para provocar o bloqueio.

Os patches, a política aprovada e o gabarito v2 foram mantidos. A análise
documenta as justificativas observáveis; não infere o raciocínio interno do
modelo nem transforma os erros em acertos. A redução de campos de agenda
também pode ter implicações de compatibilidade, mas não demonstra por si
só exposição indevida. A compatibilidade técnica foi validada separadamente
antes da bateria; a referência de privacidade declara permissões, sem
certificar automaticamente o comportamento em execução.

## Repetições e desvios de roteiro

Vinte de 24 pares R1/R2 concordaram (83,3%). Quatro pares divergiram e receberam
R3, conforme o protocolo congelado. As quatro R3 persistiram pareceres:
duas recomendações de liberar e duas de bloquear. Uma delas corrigiu por
iniciativa própria uma chamada inicial sem token. R3 não substitui R1/R2,
não resolve retroativamente a inconclusiva e não entra nas métricas principais.

Duas conversas principais fizeram chamadas extras de descoberta de metadados.
Uma consultou as listas gerais do aplicativo; outra tentou os métodos de
recursos e templates do Filesystem, que responderam `method not found`.
Depois, ambas chamaram a ferramenta pedida e receberam o bloqueio antes do
backend. As chamadas extras e o erro de script mencionado pelo modelo foram
preservados na evidência privada. Os dois pedidos seguintes permaneceram
iguais ao protocolo; nenhuma instrução corretiva extra foi enviada.

## Tempos e consumo

Nas 48 revisões principais, a soma das durações dos três turnos teve mediana
de 28,0 s e média de 41,9 s por revisão, com intervalo de 15,8 a 87,8 s.
As pausas entre turnos tiveram mediana de 13,5 s e média de 19,4 s.
O intervalo observado entre início do primeiro turno e fim do terceiro teve
mediana de 46,0 s e média de 61,2 s. Preparação, troca de patch e restauração
ficam fora dessa duração de turnos. Os timestamps e a duração contabilizada
podem ter pequenas diferenças de precisão.

Os turnos incluem modelo, chamadas de ferramentas e esperas internas;
não são latência pura da IA. As pausas incluem orquestração e espera do
operador, não apenas tempo humano. Os tempos locais do gateway estão dentro
dos turnos e não devem ser somados novamente.

| Tokens das 48 revisões principais | Contagem |
|---|---:|
| Entrada | 15.133.300 |
| Entrada em cache, incluída acima | 13.505.536 |
| Entrada sem cache | 1.627.764 |
| Saída | 37.938 |
| Raciocínio, incluído na saída | 1.375 |
| Entrada + saída | 15.171.238 |

Contagens vieram de `turn_token_usage`, com três turnos por conversa e soma
conferida contra o total de cada conversa. As quatro diagnósticas consumiram
separadamente 1.543.281 tokens de entrada + saída. Esses dados não são uma
fatura e não estabelecem custo monetário da assinatura.

Há 240 observações principais de inspeção instrumentada. A mediana da
verificação de integridade foi 45,2 ms e a média 3.418,8 ms; o Filesystem
possui milhares de arquivos e pode dominar a média. Montagem de dossiê:
mediana 3,6 ms; persistência da evidência: 10,3 ms. Persistência de parecer:
mediana 5,8 ms em 47 observações. São operações, não 240 revisões independentes.
Esta bateria bloqueia antes do backend e não mede sua latência de inicialização;
os controles nativos anteriores estão no relatório de validação técnica.

## Integridade e próximos refinamentos

A auditoria conferiu os 24 patches, pedidos e ordem congelados, gabarito v2,
modelo/esforço efetivos, aprovação e envelope preservados em cada conversa,
16 módulos idênticos entre fonte, wheel e instalação, e restauração final
dos códigos e estados aprovados. Git, Filesystem e Donna ficaram `ready`,
com 11, 4.078 e 15 arquivos protegidos, respectivamente.

Os resultados sugerem melhorar a mensagem de campo obrigatório ausente,
esclarecer a diferença entre declaração de privacidade e conformidade
observada, e orientar a avaliação de regressão e escopo por ferramenta.
Esses refinamentos ainda não foram aplicados à versão testada. A exigência
de vínculo válido e a aprovação humana para executar devem continuar.

Esta série avalia a combinação 0.11.0/Luna low. As séries históricas e a
revisão preliminar isolada da 0.10.0 permanecem separadas. Continuam válidos
os limites das conferências diretas dos ataques em descrições e do isolamento
por pastas/sandbox no mesmo usuário Windows. Nenhum resultado foi repetido
para obter uma decisão desejada. Não houve commit ou push.
