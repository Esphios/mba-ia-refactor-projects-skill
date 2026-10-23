# Baseline da entrega

- Revisão original: `6d1ce6248c3e956801010a89d8bdaab48029bf30`
- Referência imutável local: `baseline/deliver-refactor-arch-6d1ce62`
- Branch de implementação: `work/deliver-refactor-arch`
- Projetos cobertos: `code-smells-project`, `ecommerce-api-legacy` e `task-manager-api`
- Alteração preexistente: somente `.gitignore`, com a inclusão das regras `.**/`, `docs/` e `openspec/`.
- Fontes preexistentes modificadas: nenhuma.
- Bancos e arquivos `.env` encontrados antes da implementação: nenhum.
- Seeds executados na preparação: nenhum.

O checkpoint por referência Git preserva o conteúdo original dos três projetos. A
alteração preexistente do usuário permaneceu no working tree ao criar a branch de
implementação. Bancos futuros continuam excluídos por `*.db` e `instance/`; arquivos
de ambiente reais continuam excluídos por `.env`.

## Procedimento de restauração

Compare qualquer projeto com a referência de baseline usando
`git diff baseline/deliver-refactor-arch-6d1ce62 -- <diretório>`. A restauração não
deve usar reset destrutivo: reverta somente os arquivos da execução e restaure uma
cópia do banco correspondente quando houver banco persistente.
