# Teste do MCP Sentry — resultados MOSTRATEC

Pacote público das duas baterias concluídas em 06/10/2026, publicado em
07/10/2026. Os relatórios e dados completos continuam na área privada do
operador. Os dados desta pasta permitem conferir as contagens e a concordância
das execuções sem publicar o gabarito por caso, os patches ou as transcrições.

## Leitura e arquivos

1. [Relatório e comparação](RELATORIO.md): método, resultados, erros e limites.
2. [Métricas por grupo](metricas_por_grupo.csv): mesma definição do analisador
   original, para as duas baterias completas; R3 e tentativa parcial excluídas.
3. [Execuções públicas](execucoes_publicas.csv): 109 registros com campos
   selecionados e identificadores anônimos, incluindo R3 e tentativa parcial.
4. [Eventos técnicos](eventos_tecnicos.csv): incompatibilidade da 0.9.0,
   correções da coleta e falha de registro preservada na série corrigida.
5. [Proveniência](proveniencia.json): hashes das fontes privadas e dos CSVs
   publicados, versão instalada, conferências e limites da publicação.

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
pares contra as métricas originais, sem alterar os arquivos de origem:

```powershell
py -3 desenvolvimento/teste_do_sentry/exportar_resultados_publicos.py `
  --raiz-privada C:\CAMINHO_PRIVADO `
  --saida pesquisa/02_resultados/04_mostratec_mcp_sentry
```

A chave de anonimização é efêmera e não é publicada nem gravada. Uma nova
exportação gera IDs diferentes; decisões, tempos e métricas permanecem os
mesmos se as fontes não mudarem. Não usar a reexportação para misturar séries
ou substituir recusas e erros. O exportador é específico deste fechamento.

Credenciais, contas, caminhos locais, IDs Google, IDs de conversas, argumentos
MCP, justificativas e fotografias não entram no pacote. Isso não anonimiza os
demais documentos já existentes no repositório. Futuras revisões continuam
em workspaces separados, sem estes resultados, gabarito ou histórico.
