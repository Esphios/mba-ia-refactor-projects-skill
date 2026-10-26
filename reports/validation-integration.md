# Validação da integração — nova execução da refactor-arch

Data: 23/10/2026. Escopo: artefatos e verificações comuns da Fase 3 aprovada.
Plano, revisão de origem e aceite: [skill-execution.md](skill-execution.md).

## Revisão e correções dentro da skill

O verificador de entrega foi criado nesta execução com testes antes da
implementação: [RED](evidence/skill-run-integration-checker-red.log) e
[GREEN](evidence/skill-run-integration-checker-green.log). Os sete casos cobrem
documentos ausentes, seções obrigatórias, exemplos apenas com comentários,
referências/links ausentes e divergência entre pacotes. Ele não prova semântica,
boot ou autoria.

A revisão independente de README/scripts encontrou:

| Achado | Correção nesta execução | Verificação |
| --- | --- | --- |
| Timeout de subprocess.run deixava descendentes vivos | Popen conserva o launcher; taskkill /PID próprio /T /F no Windows, killpg de sessão própria em POSIX; espera o término. | Teste pai+filho descartável falha com o comportamento anterior e passa com run_owned. |
| Promessa de log sanitizado sem sanitização | Runner identifica logs como brutos locais sujeitos à revisão antes de compartilhar; não imprime ambiente. | Revisão de help/implementação. A evidência versionada precisa de inspeção própria. |
| Versão Python não registrada | python --version por ambiente, além de pip freeze. | Etapas explícitas do runner. |

Regressão do timeout: [RED](evidence/skill-run-integration-timeout-red.log).
O RED foi uma reprodução controlada com a função anterior, sem reverter fontes
de aplicação; pai e filho pertenciam ao próprio teste e foram encerrados inclusive
no caminho de falha. [Suíte raiz GREEN](evidence/skill-run-integration-tests-green.log):
**8 testes passaram**. O revisor independente repetiu os oito com o mesmo resultado.
Cleanup executado no Windows; POSIX e interrupção por teclado tiveram revisão
estática, sem afirmação de execução nesses ambientes.

## Repositório remoto

[Metadados GitHub](evidence/skill-run-integration-remote.json) consultados por API:
repositório público, fork de devfullcycle/mba-ia-refactor-projects-skill e branch
padrão main. Após a publicação, a única branch remota é `main`; sua revisão foi
conferida contra a entrega local.

## Aceite agregado

O candidato de publicação foi aberto em worktree detached limpo. `scripts/reproduce.py`
criou dois virtualenvs, executou instalações por manifest/constraints e `npm ci`,
registrou versões e rodou 19 etapas. Todas retornaram zero: checker, oito testes
de integração, 66 testes/19 contratos da loja, 21 testes/3 contratos do LMS e 28
testes/22 contratos do Task Manager. Todas as matrizes confirmaram cleanup dos
filhos e dados temporários. [Resumo sanitizado](evidence/skill-run-clean-reproduction-summary.json).

Os logs brutos de instalação ficaram fora do repositório porque podem conter
caminhos locais/URLs de pacote; o resumo foi conferido contra `summary.json` e os
logs finais. O worktree permaneceu sem alterações rastreadas.
