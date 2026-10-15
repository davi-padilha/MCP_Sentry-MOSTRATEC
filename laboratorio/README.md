# Laboratório local

Área para instalações e execuções descartáveis dos testes do MCP
Sentry. `execucoes/` preserva os registros das validações da distribuição.
Crie as subpastas conforme houver
necessidade, sem espalhar novas instalações e caches pela raiz do repositório.

```text
laboratorio/
  instalacoes/       # Código e dependências dos servidores, separados por versão
  dados/            # Arquivos, agenda e repositórios fictícios para os testes
  execucoes/        # Uma pasta por execução, com configuração, logs e resultados
  caches/           # Downloads npm/pip, se necessários
```

As subpastas geradas são ignoradas pelo Git. Os scripts reproduzíveis continuam
em `desenvolvimento/gateway/testes/`; o pacote e seu ambiente ficam em `desenvolvimento/gateway/`. Para os
clientes reais, o estado confiável de aprovação deve ficar em local protegido
contra escrita pelo agente, fora desta área de trabalho. Estados de fixtures
técnicas podem ficar em `execucoes/`, mas não comprovam essa proteção.

As instalações, resultados e evidências brutas antigas de `.lab-smoke` foram
excluídos com autorização do usuário. Os registros textuais em
`documentacao/validacoes/VALIDACAO_*.md` são resumos históricos. Para repetir os testes, recrie
as instalações com as versões documentadas e gere novos planos de execução.

Resultados necessários à etapa 4 devem ser preservados deliberadamente em um
local definido no protocolo, pois esta área não é um arquivo de evidências.

## Limpeza das validações de distribuição

Os arquivos `suite.txt`, registros de instalação/upgrade, SDK, resultados em
JSON e snapshots fictícios das execuções são preservados. As pastas `.venv`
geradas dentro de `execucoes/` podem ser removidas depois que os processos
terminarem: elas são recriáveis e não são evidências científicas. O manifesto
`LIMPEZA_AMBIENTES.json` registra os caminhos e bytes removidos nesta limpeza.

Em 14/10/2026 foram removidos 35 ambientes `.venv` das validações 1.2/1.3 e
as instalações locais antigas 1.2.0 e 1.3.0, liberando aproximadamente 456 MiB.
A instalação 1.3.1 usada por Codex e Claude foi preservada. Relatórios,
snapshots e estados das rodadas permanecem nas pastas de execução.
O manifesto desta manutenção fica em
`execucoes/limpeza-repo-2026-10-14/LIMPEZA_AMBIENTES.json`.
Para repetir validações antigas, recrie os ambientes a partir dos wheels
preservados; os caminhos antigos de Python nos registros históricos não
representam instalações ainda disponíveis.
