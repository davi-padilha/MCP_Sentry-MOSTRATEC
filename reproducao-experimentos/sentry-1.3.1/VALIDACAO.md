# Validação desta publicação — 16/10/2026

Verificações sem execução de modelos, backends protegidos ou chamadas Google:

- Exportação por lista permitida a partir dos manifestos privados de encerramento conferidos por hash: 192 principais, 8 R3, 2 tentativas técnicas, 602 turnos. Acertos principais conferidos com gabarito v2: 34, 44, 46 e 48.
- Tokens por turno reconciliados com a medição privada e, depois, tokens/durações por tentativa e grupo reconciliados novamente somente a partir dos arquivos públicos. Hashes de cada arquivo público conferidos.
- Ausência de chave/mapa HMAC, 202 IDs privados e IDs de conversa nos arquivos de resultados; inspeção de campos publicados e busca de caminhos pessoais/credenciais. A exportação não copia transcrições nem justificativas.
- 24 hashes de patches comparados com os congelamentos das quatro campanhas, sem divergências.
- Inicialização Windows em pasta nova, com `--sem-instalar`, gpt-6.1-sol/low. Baselines extraídos byte a byte: Git 11 arquivos, Filesystem 4078 e Donna 15. Fragmento TOML válido com seis interfaces, timeouts e caminhos locais.
- `git apply --check` dos 24 patches sobre os três baselines: todos aplicáveis. Nenhuma variante executada.
- Nove testes do seletor: seleção completa, duplicidade de posição, modelo errado, turnos repetidos, inconclusiva sem recibo preservada, conclusivo sem recibo recusado, R3 sem divergência recusada, técnica sem autorização recusada e mudança de evidência detectada.
- Compatibilidade EOL do pacote compartilhado: 23 conversões LF→CRLF comprovadas contra os hashes históricos; patches/archives inalterados. Nenhum arquivo do pacote 1.0.0 modificado.
- Links locais dos novos documentos conferidos.

Não foi feita instalação nova de dependências por rede, autenticação Google nem uma quinta campanha de modelos. A aplicação efetiva de aprovação/congelamento e a execução ao vivo ficam para cada réplica autorizada; não são certificadas pela validação estática. Auditoria de conversa no seletor é manual e deve ser feita nas fontes.

Para repetir as verificações públicas, dentro desta pasta:

```powershell
py -3.14 -B scripts/bateria.py verificar
py -3.14 -B scripts/verificar_publicacao.py
py -3.14 -B scripts/test_selecao.py
```
