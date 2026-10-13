# Solução de problemas

Comece pela mensagem final do instalador: ela distingue instalação do
programa e configuração do MCP. Os comandos de instalação abaixo são
executados na pasta extraída do ZIP. Para usar os comandos do programa
instalado, consulte [Uso e atualização](USO-E-ATUALIZACAO.md).

| Situação | Ação |
|---|---|
| Python não encontrado ou atalho da Store inválido | Instale Python 3.11+ com venv/pip pelo [site oficial](https://www.python.org/downloads/windows/), ou execute `.\arquivos-instalacao\instalar.ps1 -PythonExe 'C:\CAMINHO\python.exe'`. |
| PowerShell bloqueou o script | Use `INSTALAR.cmd`, que ajusta a execução somente para esse processo, ou a alternativa manual em [Uso e atualização](USO-E-ATUALIZACAO.md). Não precisa alterar a política global. |
| Arquivo ausente ou hash diferente | O instalador confere todos os arquivos entregues antes de instalar. Extraia novamente o ZIP oficial; não altere a lista de somas para ocultar a divergência. |
| Ambiente existente incompatível | Preserve-o. Escolha outro `-Ambiente` ou confira seu Python antes de atualizar; o instalador não apaga nem recria ambientes existentes automaticamente. |
| Programa instalado, MCP ainda desconectado | Abra `setup` pelo comando apresentado no resumo. Consulte [Conectar um MCP](USO-E-ATUALIZACAO.md#conectar-um-mcp). |
| Atualização da 1.0.0 ou instalação antiga | Encerre as conexões e execute `.\arquivos-instalacao\instalar.ps1 -Ambiente 'C:\PASTA_ANTERIOR\.venv' -SemConfigurar`. Não repita a aprovação inicial. |
| Pasta extraída apagada depois de instalar | Na instalação padrão nova, o programa e os guias ficam em `%LOCALAPPDATA%\MCP-Sentry-Gateway`. Instalações antigas que guardam a `.venv` na pasta extraída precisam preservar essa pasta. |
| Configuração não concluída | A instalação do programa pode ter passado. Leia o diagnóstico do setup; suas confirmações e o backup continuam obrigatórios. |
| Setup não reconhece a entrada | Use a preparação manual em CONFIGURACAO.md; preserve a configuração original. |
| Claude Desktop não encontrado ou mais de uma configuração detectada | Confira Edit Config nas configurações de desenvolvedor e informe `setup --client claude-desktop --claude-config 'CAMINHO'`. |
| Claude ainda mostra ferramentas antigas | Encerre completamente e reabra o aplicativo; teste em uma conversa nova e confira os dois conectores. |
| Claude recusou analisar sem chamar a ferramenta de revisão | Registre a recusa como comportamento do cliente/modelo; ela não comprova falha no transporte do Sentry. |
| Servidor requer segredo | Forneça a variável de ambiente indicada por nome; não ponha o valor no manifesto ou nos arquivos inspecionados. |
| Referência inicial ausente | Confira o código e faça a aprovação inicial pelo operador. |
| MCP bloqueado após mudança | Peça revisão e registro; confira o parecer e decida pelo terminal. Não inicie diretamente para contornar o bloqueio. |
| Registro sem token | Complete os campos apontados. Se não tem o token da leitura nesta conexão, solicite nova leitura de evidências. |
| Token inválido, evidência vencida ou código mudou | Releia a revisão corrente. Não invente IDs/hashes nem reutilize vínculo antigo. |
| Encerramento da conexão perdeu o token | Faça nova leitura na nova conexão antes de registrar. |
| `doctor` indica `needs_attention` | Leia os motivos. Confira arquivos, runtime, envelope e entradas do cliente antes de alterar o estado. |
| Inicialização Filesystem lenta | Há cópia/verificação de milhares de arquivos. Confira timeout do cliente; não desative a verificação para acelerar. |
| Nova autorização com backend antigo aberto | Reconecte a execução para iniciar a versão revisada. |
| Uma chamada funcionou e a seguinte foi bloqueada | Confira o alcance: uso único é consumido por uma chamada, inclusive prévia. Para continuar usando a mesma versão, escolha a aceitação permanente após revisão e confirmação próprias. |
| Aprovação genérica no chat não liberou | O cliente deve distinguir aceitação da versão de uso único e pedir a confirmação separada correspondente. Confira se o modo pelo chat está habilitado nas duas entradas. |
| Aceitação pelo chat recusou configuração ou catálogo | O aceite de código não promove essas mudanças. Use a preparação e a aprovação separadas do operador. |
| Evidência de aceitação ausente ou divergente | Preserve o estado, confira seus registros e backup; não apague a referência nem recrie uma aprovação para esconder a falha. |
| Restauração encontrou conflito | Preserve sua edição; compare com o backup e restaure manualmente somente a entrada desejada. |

Não apague estado ou aprove novamente apenas para eliminar um bloqueio.
Para solicitar ajuda, registre versão, comando, mensagem de erro e cliente,
removendo segredos e dados pessoais. O estado e os relatórios podem conter código;
compartilhe apenas os trechos necessários após conferência.
