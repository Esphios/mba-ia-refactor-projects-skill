# Validação — task-manager-api

Execução da Fase 3 de `refactor-arch` em 23/10/2026. A [auditoria](audit-project-3.md) e
a aprovação **“Aprovo o escopo completo apresentado”** foram persistidas antes das
fontes.

## Resultado medido

- Python 3.12.10, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, Flask-Cors 4.0.0,
  SQLAlchemy 2.1.6, Werkzeug 3.1.9 e pytest 9.1.1 medidos em ambiente novo.
- **28 testes passaram**, sem skip; warnings de deprecation são erros.
- **22 métodos/caminhos** passaram por HTTP real, com **34 casos adicionais de
  segurança**, processo/porta/banco próprios e cleanup confirmado.
- As 15 fontes originais, já parcialmente organizadas, ganharam Controllers,
  factory/init explícitos, security, store, validação/erros e regras compartilhadas.

Evidências: [runtime](evidence/skill-run-project-3-runtime.json),
[RED original](evidence/skill-run-project-3-red.txt),
[testes finais](evidence/skill-run-project-3-final-tests.txt),
[HTTP final](evidence/skill-run-project-3-http-final.json) e
[compatibilidade/deprecations](evidence/skill-run-project-3-api-compatibility.md).

## Achados e contratos

| Grupo | Transformação e verificação |
| --- | --- |
| T01/T02/T04 | Password removido de toda serialização; segredo/SMTP externos; scrypt e token assinado/expirável; MD5 somente antes de cutoff controlado, login correto e conta ativa. Unicode, adulteração e ausência de fallback cobertos. |
| T03 | Autorização usa conta/papel atuais. User vê/modifica o próprio escopo; manager gerencia tarefas/categorias e relatórios; admin também altera role/active e exclui usuários. Sucesso e recusas exercitados. |
| T05/T08/T10 | Routes adaptam HTTP, Controllers orquestram e store/models persistem; validação rejeita bool/tipos inválidos, preserva null/omitido/defaults e serializers específicos mantêm formas originais. |
| T07/T11 | Factory/import sem criar schema; init/seed explícitos. Seed é transacional, exige confirmação/destino e rollback foi injetado nas quatro etapas. |
| T09 | Consultas medidas, original pequeno→grande: tasks 4→44, users 5→25, categories 2→22, summary 20→40; final: 2→2, 2→2, 2→2 e 9→9, incluindo autenticação. |
| T06/T12/T13 | Debug externo e seguro por padrão; valores/regras centralizados; imports e nomes mortos/obscuros corrigidos. |

Todos os **13 achados iniciais** foram tratados: 2 CRITICAL, 5 HIGH, 4 MEDIUM
e 2 LOW. Após medir Python 3.12/SQLAlchemy 2.1, `datetime.utcnow()` e `Query.get()`
foram confirmados como APIs deprecated e substituídos dentro das transformações já
aprovadas, sem alterar retrospectivamente a contagem da auditoria somente leitura.

Preservados: 22 paths/métodos; formas e mensagens específicas; senha mínima 4;
datas UTC ingênuas nas respostas; SQLite LIKE/coringas/Unicode; user deletion
admin-only preserva a política original de excluir suas tarefas; category delete
desvincula tarefas; sem paginação, filtros, regras de cor ou formatos novos.

## Ciclos RED/GREEN e revisão

Cinco casos RED iniciais cobriram factory, hash exposto, ausência de auth, bool e
escalada. A matriz final cobre papéis/propriedade, papel e status alterados entre
requisições, cutoff/clock, MD5, Unicode, null/omitido, seed/rollback e crescimento
de queries. A revisão de contrato encontrou 404/405 HTML e `active` aceito no
cadastro público; os testes falharam antes da correção e passaram depois.

A revisão independente encontrou uma base legada permitida com `tasks.status=NULL`:
o detalhe marcava a tarefa vencida, mas stats/summary a omitiam por semântica SQL de
`NOT IN`. O [RED](evidence/skill-run-project-3-null-status-red.txt) reproduziu a
divergência contra o original. Os dois predicados agora incluem NULL explicitamente;
o [GREEN](evidence/skill-run-project-3-null-status-green.txt) confirma detalhe,
stats e summary coerentes.

A revisão final encontrou reutilização de IDs pelo SQLite: um token de uma conta
excluída podia autenticar uma nova conta criada com o mesmo ID. O
[RED](evidence/skill-run-project-3-token-reuse-red.txt) reproduziu leitura e
alteração indevidas. O token agora inclui um identificador HMAC da instância da
credencial e a validação o compara com a conta persistida atual, sem exigir
migração de schema. O
[GREEN](evidence/skill-run-project-3-token-reuse-green.txt) cobre exclusão e
recriação de contas comuns e administrativas; tokens emitidos antes da correção
são recusados.

## Migração, rollback e limites

O [README do projeto](../task-manager-api/README.md) documenta configuração,
init/seed, backup, cutoff, migração e rollback. Nenhuma base real/SMTP foi tocada.
Tokens falsos antigos deixam de funcionar; MD5 não migrado até o cutoff requer
reset administrado. Código legado não autentica hashes modernos, então rollback
exige verificador compatível ou backup sob plano de perda de dados. Não é load test,
teste de TLS nem avaliação de servidor WSGI de produção.

Comandos, dentro do projeto:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tests/run_http_matrix.py
```
