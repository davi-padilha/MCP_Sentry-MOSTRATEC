# Comparação e diagnóstico do protótipo

O gateway 0.11.0 com Luna/medium registrou todos os 48 pareceres principais,
acertou 47 classificações e bloqueou uma benigna. A mesma versão com low
havia acertado 39, bloqueado oito benignas e produzido uma inconclusiva.
No gateway 0.9.1 com medium, houve 47 acertos e uma inconclusiva.

| Medida, sempre 48 principais | 0.9.1 / medium | 0.11.0 / low | 0.11.0 / medium |
|---|---:|---:|---:|
| Acertos frente ao gabarito v2 | 47 | 39 | 47 |
| Benignas bloqueadas | 0 | 8 | 1 |
| Malignas liberadas | 0 | 0 | 0 |
| Inconclusivas | 1 | 1 | 0 |
| Pareceres persistidos | 47 | 47 | 48 |
| Pares R1/R2 concordantes | 23/24 | 20/24 | 23/24 |

Na nova série, 22/22 malignas recomendaram bloquear e 25/26 benignas
recomendaram liberar: 97,9% de acerto no total. A taxa de bloqueio de benignas
foi 1/26 (3,8%). Todos os recibos principais e o da R3 conferiram com a
persistência. Recomendação de liberar não autoriza execução nem muda baseline;
nenhum backend alterado foi iniciado em qualquer das três baterias.

## Comparação dos mesmos casos

Foram conferidos os hashes dos 24 patches, dos pedidos e da ordem nas três
séries. O conteúdo das políticas também é igual. Nas duas séries 0.11.0,
o hash do wheel é idêntico; os 16 módulos instalados coincidem com fonte e
wheel. As raízes foram relocalizadas para uma série independente, mantendo
o código nativo e as políticas. O gabarito v2 já estava congelado nas séries
0.11.0; na série antiga, a comparação usa a reavaliação previamente documentada.

De low para medium no mesmo gateway, sete bloqueios de benignas passaram
a decisões corretas e a inconclusiva passou a um parecer correto persistido.
Um bloqueio de benigna permaneceu, e as 39 decisões já corretas continuaram
corretas. De 0.9.1/medium para 0.11.0/medium, a inconclusiva antiga foi
resolvida, mas uma benigna antes liberada foi bloqueada. As outras 46
classificações permaneceram corretas. Os totais de acerto são iguais entre
as duas condições medium, mas o tipo de erro mudou.

O único par divergente desta rodada recebeu R3, que recomendou liberar.
O bloqueio de R2 continua nas métricas; R3 é diagnóstico e não substituição.
Isso documenta variação de julgamento com a mesma condição e o mesmo patch.

## O que corrigir no gateway e o que envolve o modelo

| Observação | Diagnóstico sustentado pela evidência | Próxima ação útil |
|---|---|---|
| Payload sem token: oito principais em low, duas em medium | O modelo omitiu campo obrigatório; o gateway rejeitou corretamente. A mensagem genérica e `recoverable: false` dificultam recuperação. | Informar campo ausente, formatos aceitos e recuperação; manter token, hashes, cobertura e validade obrigatórios. Conferir como o cliente apresenta o esquema com dois formatos. |
| Bloqueio de uma benigna nos dois níveis | Os pareceres alegaram falta de verificação de caminhos/erros. Não identificaram nova exposição causada pelo patch. R1 e R3 medium liberaram, reconhecendo a validação preservada. | Explicar separadamente mudança introduzida, risco demonstrado e limitação da evidência. Mostrar contexto relevante de validadores no dossiê, com vínculo de integridade e tratamento como conteúdo não confiável. |
| Outros sete bloqueios de benignas em low foram corrigidos por medium | A classificação é sensível ao nível de raciocínio e à interpretação do contexto. A versão e a política do gateway são as mesmas. | Melhorar clareza e testar a apresentação nos dois níveis; não considerar medium garantia de decisão correta. |
| Registro completo na nova série medium | Dois erros de formato foram corrigidos pelo próprio modelo. Nenhum vínculo incompleto foi aceito. | Preservar a validação de segurança e os recibos auditáveis; medir acerto na primeira tentativa além de persistência final. |
| Conexões recriadas durante fechamento antes da revisão 33 | Falha operacional de gerenciamento de sessões no experimento, separada da classificação. O preparador parou antes de aplicar o próximo patch. | Fechar sessões concluídas de forma confiável antes de trocar o estado; registrar reconexão e carga do cliente. |
| Tempo total maior com medium, etapas locais similares | Duração dos turnos inclui modelo, ferramentas e esperas internas. Houve turnos longos e acúmulo de sessões. | Medir espera do cliente/transporte e tempo das chamadas separadamente; evitar atribuir todo o atraso ao gateway. |

O bloqueio residual afirmou que a alteração parecia limitada e razoável,
mas que as evidências não verificavam o confinamento dos caminhos e os erros.
A revisão estática privada confirmou a chamada ao validador preservada antes
da leitura e ausência de ampliação de diretórios. A R3 usou esse ponto para
recomendar liberar. O resultado é um falso bloqueio frente ao gabarito
controlado, com incerteza expressa pelo modelo; não foi constatada uma falha
do código de isolamento do gateway nesse caso.

Ausência de certificação de privacidade ou de observação em runtime é uma
limitação da evidência. Ela deve permanecer explícita, mas não implica
automaticamente que toda alteração introduziu um ataque. Aprovar uma
referência também não certifica sua privacidade. A revisão precisa avaliar
a política e as mudanças concretas, inclusive eventuais problemas já existentes.

As duas chamadas inválidas medium omitiram `review_token`, usando apenas
decisão, justificativa e riscos. Ambas foram corrigidas dentro do mesmo turno
por iniciativa do modelo, sem mensagem extra do supervisor. Foram 50
tentativas para 48 registros principais. A inconclusiva medium antiga usava
identificadores incorretos; o token evita copiá-los, mas ainda precisa ser
enviado corretamente. Sua conveniência não deve remover a amarração à
evidência lida nem permitir aprovação automática.

O defeito histórico de mascaramento que deformava literais já havia sido
corrigido. Na nova rodada, a conferência do diff confirmou os marcadores
literais preservados nas duas repetições, que medium liberou. Isso ajuda a
separar aquele defeito concreto do gateway das dúvidas posteriores do modelo
sobre a cobertura de uma máscara adicional.

## Tempos e consumo

| Medida das principais | 0.9.1 / medium | 0.11.0 / low | 0.11.0 / medium |
|---|---:|---:|---:|
| Mediana da soma dos três turnos | 31,9 s | 28,0 s | 37,1 s |
| Média da soma dos três turnos | 45,6 s | 41,9 s | 60,3 s |
| Maior soma dos três turnos | 97,5 s | 87,8 s | 320,3 s |
| Entrada total | 14.228.587 | 15.133.300 | 14.425.306 |
| Entrada em cache, incluída acima | 12.695.040 | 13.505.536 | 12.785.920 |
| Saída total | 53.418 | 37.938 | 49.278 |
| Raciocínio, incluído na saída | 15.432 | 1.375 | 15.559 |

As contagens novas vieram de `turn_token_usage`, com três turnos por conversa
e soma conferida contra o total. A apuração histórica usou o total acumulado
final por conversa, conforme o relatório daquela série. Contagens não são
fatura nem consumo monetário comprovado da assinatura.

Nesta rodada medium, a mediana das pausas entre turnos foi 13 s, e a média
17,4 s. O intervalo observado completo teve mediana 49,5 s e média 77,7 s.
A preparação, troca de patch e restauração ficam fora das durações de turnos.
As durações incluem modelo, ferramentas e espera interna; as pausas incluem
orquestração e operador. Tempos do gateway estão dentro dos turnos e não
devem ser somados novamente. O incidente de sessões limita a interpretação
de desempenho: não se afirma que todo o aumento seja causado por medium.

Nas 240 inspeções principais instrumentadas, a verificação de integridade
teve média de 3.399,7 ms, semelhante aos 3.418,8 ms de low. Montagem de dossiê:
mediana 4,1 ms; persistência da evidência: 10,4 ms; persistência de parecer:
5,8 ms. As distribuições por operação estão nos arquivos de dados. Não são
240 revisões independentes nem medições de inicialização do backend,
que permaneceu bloqueado. O custo de leitura do grande catálogo Filesystem
continua sendo candidato a otimização com controles próprios de integridade.

## Encerramento e limites

Antes da revisão 33, o fechamento encontrou conexões de teste recriadas.
Foram arquivadas reversivelmente 32 conversas medium já concluídas e 52
conversas low concluídas, preservando dados e movendo os rollouts para o
arquivo do Codex. Após o arquivamento, restavam 12 processos da série;
o encerramento restrito a esses processos confirmou zero. A coleta retomou
sem alterar gateway, política, casos, gabarito, modelo ou mensagens. As
conversas concluídas restantes também foram arquivadas para controlar carga.
O exportador verifica a identidade da sessão e lê o rollout arquivado quando
o caminho anterior foi movido. O incidente foi registrado fora dos resultados
do modelo; nenhuma conversa de revisão teve chamada fora do roteiro.

Os três códigos e estados aprovados foram restaurados e conferidos. Git,
Filesystem e Donna ficaram `ready`, com 11, 4.078 e 15 arquivos protegidos.
As verificações técnicas da mesma versão foram reutilizadas após conferir
os bytes; nenhuma correção foi introduzida no gateway durante esta bateria.

Esta comparação orienta a evolução do protótipo. Duas repetições por caso,
variação do modelo, diferenças de apresentação e condições do cliente não
permitem atribuir cada mudança de resultado a uma causa única. As referências
e dados são fictícios, com isolamento por pastas/sandbox no mesmo usuário
Windows; os limites das conferências diretas dos casos de descrição continuam
registrados no protocolo. Todos os resultados anteriores e o gabarito v2
foram preservados. Sem commit ou push.
