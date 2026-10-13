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
