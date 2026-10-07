# Teste do MCP Sentry — resultados MOSTRATEC

Pacote público das duas baterias concluídas em 06/10/2026, publicado em
07/10/2026. Os relatórios e dados completos continuam na área privada do
operador. Os dados desta pasta permitem conferir as contagens e a concordância
das execuções sem publicar o gabarito por caso, os patches ou as transcrições.

## Leitura e arquivos

1. [Relatório e comparação](RELATORIO.md): método, resultados, erros e limites.
2. [Métricas por grupo](metricas_por_grupo.csv): gabarito revisado v2, para as
   duas baterias completas; R3 e tentativa parcial excluídas. A leitura v1 está
   em [métricas históricas](metricas_por_grupo_historicas.csv).
3. [Execuções públicas](execucoes_publicas.csv): 109 registros com campos
   selecionados e identificadores anônimos, incluindo R3 e tentativa parcial.
4. [Eventos técnicos](eventos_tecnicos.csv): incompatibilidade da 0.9.0,
   correções da coleta e falha de registro preservada na série corrigida.
5. [Proveniência](proveniencia.json): hashes das fontes privadas, gabaritos
   v1/v2 e CSVs publicados, conferências e limites. A
   [proveniência histórica](proveniencia_historica.json) conserva a publicação v1.
6. [Tempos e consumo do Luna](TEMPOS-E-CONSUMO.md): apuração posterior dos logs,
   estimativas com ressalvas e propostas de melhoria do gateway.
7. [Reavaliação da classificação de agenda](REAVALIACAO-CLASSIFICACAO.md):
   reclassificação autorizada, conclusão semântica e efeitos nas duas baterias.
8. [Tokens e tempos das 109 conversas históricas](TOKENS_E_TEMPOS.md):
   contadores por turno e série, cache, tamanho dos dossiês e duração;
   primárias, R3 e tentativa parcial separadas, sem novas revisões.

Em 07/10/2026, o operador autorizou uma correção posterior à coleta: uma
variante passou de bloquear para liberar. O gabarito v2 tem 13 benignas e
11 malignas. Nenhum parecer ou registro executado mudou; somente a comparação
com a classe esperada. As métricas históricas permanecem disponíveis.

Na proveniência histórica, o nome `metricas_por_grupo.csv` corresponde à
primeira exportação; seu hash é o do arquivo agora preservado como
`metricas_por_grupo_historicas.csv`. A proveniência atual lista ambos os nomes.

## Séries

| Identificador | Modelo / raciocínio | Sentry | Uso |
| --- | --- | --- | --- |
| sol_081 | GPT-6.1 Sol / médio | 0.8.1 | 48 primárias; comparação principal |
| luna_091 | GPT-6 Luna / médio | 0.9.1 + políticas | 48 primárias + 1 R3 diagnóstica |
| luna_090_parcial | GPT-6 Luna / médio | 0.9.0 + políticas | 12 execuções; tentativa interrompida por defeito técnico |

## Campos do registro público

`caso_anonimo` liga R1, R2 e eventual R3 somente dentro da mesma série. Não
corresponde a um nome original; os IDs não fornecem correspondência entre séries.
Os registros estão ordenados por esse identificador: sua posição não indica
a ordem sorteada, que foi preservada privadamente.

`parecer_registrado` contém `liberar`, `bloquear` ou vazio. Vazio com
`inconclusivo=sim` significa ausência de parecer persistido; não implica
necessariamente recusa de analisar. `uso` separa `principal`, `diagnostico`
e `parcial_tecnica`. Os campos modelo/esforço/versão identificam as séries;
os contextos efetivos foram auditados nos registros privados.

`tempo_min` conserva o intervalo registrado entre o início e o fim dos três
turnos. Inclui espera e acompanhamento do operador; não é latência pura do
modelo, custo de API ou medida comparável de desempenho computacional.

Não há coluna de classe esperada por caso. Assim, inconclusivos, ausência de
execução e concordância R1/R2 podem ser recalculados publicamente; as taxas de
benignas bloqueadas e malignas liberadas exigem o gabarito privado. Seus
agregados são publicados e têm hashes vinculados às fontes. Um hash não
substitui a inspeção da fonte nem demonstra sozinho a validade do gabarito.

## Exportação

O [exportador](../../../desenvolvimento/teste_do_sentry/exportar_resultados_publicos.py)
usa uma lista explícita de campos permitidos. Ele confere os totais e os
pares e publica a v1 e a v2 separadamente, sem alterar as fontes congeladas:

```powershell
py -3 desenvolvimento/teste_do_sentry/exportar_resultados_publicos.py `
  --raiz-privada C:\CAMINHO_PRIVADO `
  --saida pesquisa/02_resultados/04_mostratec_mcp_sentry `
  --reavaliacao C:\CAMINHO_PRIVADO\operador\reavaliacao-20261007
```

A chave de anonimização é efêmera e não é publicada nem gravada. Uma nova
exportação gera IDs diferentes; decisões, tempos e métricas permanecem os
mesmos se as fontes não mudarem. Nesta reavaliação os registros públicos e
seus IDs foram mantidos byte a byte: só os agregados e a proveniência mudaram.
O exportador recusa substituir uma publicação revisada pela leitura histórica
sem o parâmetro de reavaliação. Não usar a reexportação para misturar séries
ou substituir recusas e erros. O exportador é específico deste fechamento.

O script [reavaliar_gabarito.py](../../../desenvolvimento/teste_do_sentry/reavaliar_gabarito.py)
criou a versão privada v2 e recalculou as duas séries, preservando hashes dos
registros, patches e gabarito original. Não executa novas revisões. O código
de criação do gabarito a partir do mapeamento original continua produzindo v1;
ele não incorpora automaticamente a reclassificação documentada.

Credenciais, contas, caminhos locais, IDs Google, IDs de conversas, argumentos
MCP, justificativas e fotografias não entram no pacote. Isso não anonimiza os
demais documentos já existentes no repositório. Futuras revisões continuam
em workspaces separados, sem estes resultados, gabarito ou histórico.
