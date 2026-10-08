# Solução de problemas

| Situação | Ação |
|---|---|
| `py` não encontrado | Instale Python ou passe seu executável a `instalar.ps1 -PythonExe`. |
| PowerShell bloqueou o script | Use os comandos de instalação manual do README; não precisa alterar a política global. |
| Hash do wheel diferente | Interrompa e obtenha novamente a distribuição. |
| Setup não reconhece a entrada | Use a preparação manual em CONFIGURACAO.md; preserve a configuração original. |
| Servidor requer segredo | Forneça a variável de ambiente indicada por nome; não ponha o valor no manifesto ou nos arquivos inspecionados. |
| Referência inicial ausente | Confira o código e faça a aprovação inicial pelo operador. |
| MCP bloqueado após mudança | Peça revisão e registro; confira o parecer e decida pelo terminal. Não inicie diretamente para contornar o bloqueio. |
| Registro sem token | Complete os campos apontados. Se não tem o token da leitura nesta conexão, solicite nova leitura de evidências. |
| Token inválido, evidência vencida ou código mudou | Releia a revisão corrente. Não invente IDs/hashes nem reutilize vínculo antigo. |
| Encerramento da conexão perdeu o token | Faça nova leitura na nova conexão antes de registrar. |
| `doctor` indica `needs_attention` | Leia os motivos. Confira arquivos, runtime, envelope e entradas do cliente antes de alterar o estado. |
| Inicialização Filesystem lenta | Há cópia/verificação de milhares de arquivos. Confira timeout do cliente; não desative a verificação para acelerar. |
| Nova autorização com backend antigo aberto | Reconecte a execução para iniciar a versão revisada. |
| Restauração encontrou conflito | Preserve sua edição; compare com o backup e restaure manualmente somente a entrada desejada. |

Não apague estado ou aprove novamente apenas para eliminar um bloqueio.
Para solicitar ajuda, registre versão, comando, mensagem de erro e cliente,
removendo segredos e dados pessoais. O estado e os relatórios podem conter código;
compartilhe apenas os trechos necessários após conferência.
