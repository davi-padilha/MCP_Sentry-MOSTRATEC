# Checklist da bateria portatil 1.0

- Ordem original: operador/ordem_sorteada.csv (nao sortear novamente).
- Modelo gpt-6-luna e esforco low, medium ou high fixos por serie; memoria desativada.
- Revisores em workspace-revisor, nunca no repo nem no operador.
- Fechar a conexao anterior; guardar evidencias antes de restaurar estado.
- Restaurar baseline/aplicar um patch; nova conversa para cada linha R1/R2.
- Enviar tarefa fixa; confirmar bloqueio inicial sem iniciar backend.
- Enviar pedido fixo de revisao; nao autorizar ferramentas de shell, catalogo ou execucao.
- Enviar pedido fixo de registro; verificar recibo persistido pelo Sentry.
- Coletar estado + exportar conversa + preencher registro.csv; arquivar conversa.
- Preservar erros/desvios e ausencias de ferramenta. Nao repetir para melhorar resultado.
- Repetir apenas falha tecnica comprovada, preservando a tentativa original.
- R3 apenas para divergencia R1/R2, separada das 48 metricas principais.
- Nunca accept-current/approve nas variantes. Restaurar os 3 baselines ao terminar.
