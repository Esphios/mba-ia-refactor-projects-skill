# Validação — Task Manager API

Data de execução: 2026-10-22 America/Sao_Paulo (logs UTC podem indicar 2026-10-23). Base Git original: `6d1ce6248c3e956801010a89d8bdaab48029bf30`; alterações locais sem commit nesta etapa. A revisão refatorada é identificada pelo [manifesto SHA-256 das fontes](evidence/project-3-refactored-hashes.json); revisão final do commit cabe à integração. [Hashes dos originais](evidence/project-3-original-hashes.json) permitem comparar com HEAD original. Escopo: todos os 22 métodos/caminhos explícitos, sem HEAD/OPTIONS automáticos.

Autorização aplicada: **“ignore as aprovações por enquanto. continue até o fim.”**. O waiver autorizou a continuação; a avaliação independente da skill é evidência separada mantida pelo integrador. Não se apresenta esta implementação como sessão de avaliação cega.

## Comandos e resultados observados

Executados a partir da raiz do repositório, em ambiente próprio `task-manager-api/.venv`, sem seed em banco existente:

```powershell
python -m venv task-manager-api/.venv
task-manager-api/.venv/Scripts/python -m pip install -r task-manager-api/requirements-dev.txt
task-manager-api/.venv/Scripts/python task-manager-api/tests/baseline.py
task-manager-api/.venv/Scripts/python -m pytest task-manager-api/tests/test_security.py -q
task-manager-api/.venv/Scripts/python -m pytest task-manager-api/tests -q -s
task-manager-api/.venv/Scripts/python task-manager-api/tests/run_http_matrix.py
task-manager-api/.venv/Scripts/python -m compileall -q task-manager-api/app.py task-manager-api/auth.py task-manager-api/config.py task-manager-api/controllers task-manager-api/models task-manager-api/routes task-manager-api/services task-manager-api/utils task-manager-api/seed.py
```

O baseline e RED foram executados antes da alteração das fontes. `tests/baseline.py` é o harness histórico aplicado ao original, não um comando de regressão do código final. Baseline: login 200, usuário anônimo acessava lista 200, senha/hash exposto e criação de tarefa 201. Contagem de blueprints 20 mais raiz/health = 22. [Log baseline](evidence/project-3-baseline.log). RED: 3 falhas reais — serializer expunha password, nova senha MD5 e ausência de factory. [Log RED](evidence/project-3-red.log). Após correções, a suíte final observou **68 passed in 63.25s**, incluindo 22 sucessos HTTP pelo test client, negações por endpoint, transações e regressões. [Log completo de testes](evidence/project-3-tests.log).

Runtime verificado: Python 3.12.10, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.6, Werkzeug 3.1.9, itsdangerous 2.2.0. As duas deprecações foram confirmadas por documentação oficial da versão aplicável, vinculada à auditoria; caminhos principais passaram com LegacyAPIWarning e DeprecationWarning tratados como erro.

## Boot real e matriz dos 22 contratos

O runner prepara SQLite em TemporaryDirectory, cria fixtures descartáveis, escolhe porta livre, inicia `python app.py` em processo filho, espera `/health`, faz chamadas urllib HTTP reais e encerra processo. Configuração SMTP desabilitada. Debug off; banco existente não é aberto. [Log sanitizado do processo e matriz](evidence/project-3-http.log). Resultado: **HTTP_MATRIX 22/22 PASS** e negações reais 401/403. Não há token, senha ou hash no log.

| Método/caminho exercitado | Status esperado | Observado |
|---|---|---|
| GET `/` | 200 | 200 PASS |
| GET `/health` | 200 | 200 PASS |
| GET `/tasks` | 200 | 200 PASS |
| GET `/tasks/1` | 200 | 200 PASS |
| POST `/tasks` | 201 | 201 PASS |
| PUT `/tasks/1` | 200 | 200 PASS |
| GET `/tasks/search?q=HTTP` | 200 | 200 PASS |
| GET `/tasks/stats` | 200 | 200 PASS |
| GET `/users` | 200 | 200 PASS |
| GET `/users/2` | 200 | 200 PASS |
| POST `/users` | 201 | 201 PASS |
| PUT `/users/2` | 200 | 200 PASS |
| GET `/users/2/tasks` | 200 | 200 PASS |
| POST `/login` | 200 | 200 PASS |
| GET `/reports/summary` | 200 | 200 PASS |
| GET `/reports/user/2` | 200 | 200 PASS |
| GET `/categories` | 200 | 200 PASS |
| POST `/categories` | 201 | 201 PASS |
| PUT `/categories/2` | 200 | 200 PASS |
| DELETE `/categories/2` | 200 | 200 PASS |
| DELETE `/tasks/1` | 200 | 200 PASS |
| DELETE `/users/3` | 200 | 200 PASS |

IDs concretos representam os caminhos parametrizados do inventário original. Todos os resultados protegidos acima usam titular/admin legítimo. A suíte adicional compara conjuntos exatos de chaves por contexto (lista, detalhe, busca, tarefas do usuário, login, usuários, categorias e relatórios), removendo somente password conforme diferença autorizada.

## Regressões e integridade

- Ausência de identidade em cada uma das 18 operações protegidas: 401; token falso/adulterado/expirado e identidade desativada: negados. Terceiros não acessam tarefas/contas/relatórios alheios. Admin acessa detalhes, relatórios e alteração legítima; titular altera e exclui sua conta.
- POST users com admin/manager: 403; PUT role/active por titular: 403; promoção por admin: 200. Roles são lidas novamente do banco a cada token verificado.
- Senhas modernas scrypt com salts distintos. Login MD5 errado e após cutoff: 401 sem upgrade; conta inativa: 403 sem upgrade; sucesso antes do cutoff: scrypt persistido; login moderno posterior: 200.
- Título 3/200 aceito, 2/201 rejeitado; tipo, prioridade, status, tags e data inválidos: 400 em create/update sem mutação. Referência inexistente: 404. Email duplicado: 409. Entrada de SQL injection no login: 401, sem bypass.
- Falha induzida de commit retorna erro sanitizado 500 e rollback; nenhuma tarefa nova persiste. Falha durante exclusão multientidade preserva usuário e tarefas. Exclusão válida de usuário remove tarefas; exclusão de categoria deixa category_id null e preserva tarefas.
- Datas naive UTC legadas e aware: normalizadas sem TypeError; igualdade não atrasa e tarefas done/cancelled não atrasam. Abertura de cópia SQLite criada com schema legado conserva IDs 7/8/9, relações, datas históricas e tags; login atualiza somente hash na cópia. Original comparado byte a byte permanece intacto.
- Factory não cria banco; seed recusa banco populado em subprocesso e mantém os registros. O import do app original no teste RED havia criado somente um SQLite novo local, ignorado/excluído da entrega, sem uso de dados existentes.
- SMTP habilitado é testado com transporte MagicMock injetado; desabilitado não chama transporte. Nenhum e-mail externo foi enviado. Falha de health é 503 sanitizado.

SELECTs medidos antes/depois da adição de 20 usuários/categorias/tarefas (1 para 21 tarefas): `/tasks` **2→2**, `/users` **3→3**, `/categories` **3→3**, `/reports/summary` **6→6**, incluindo autenticação. joinedload das relações de tarefa e selectinload das coleções tornam o crescimento limitado; o log registra ambas as medições. Listagens ainda retornam todos os resultados conforme implementação original, sem promessa de paginação ou teste de carga.

## Reauditoria e resolução por achado

| Achado | Resultado e evidência de correção |
|---|---|
| P3-01 CRITICAL | Corrigido: whitelist User.to_dict sem password; shapes e varredura de respostas em tests/test_contracts.py |
| P3-06 HIGH | Corrigido: scrypt em models/user.py e migração MD5 condicionada em controllers/user_controller.py; testes legacy/cutoff/inactive |
| P3-07 HIGH | Corrigido: auth.py valida assinatura/expiração, carrega conta ativa atual e aplica owner/admin; configuração SECRET_KEY externa; matriz de negações e sucessos |
| P3-08 CRITICAL | Corrigido: NotificationService depende de ambiente, fica off por padrão e aceita transporte injetado; testes sem SMTP real |
| P3-02 MEDIUM | Corrigido: models/repository.py centraliza eager loading; contagens 1/21 constantes comprovadas |
| P3-03 MEDIUM | Corrigido: utils/validation.py, serialization.py e dates.py compartilhados; limites e shapes preservados |
| P3-09 MEDIUM | Corrigido: Session.get, selects ORM e utc_naive; testes warnings-as-errors e banco legado |
| P3-04 LOW | Corrigido: imports sem uso removidos dos handlers/utilitários; compile e boot reais passam |
| P3-05 LOW | Corrigido: PRIORITIES, DEFAULT_PRIORITY e HIGH_PRIORITY_MAX compartilham os mesmos valores originais |

MVC verificado por fluxo: routes/task_routes.py → controllers/task_controller.py → models/repository.py/Task → utils/serialization.py; usuários/categorias/relatórios seguem o mesmo limite. Rotas não importam db/modelos, executam SQL ou regras de negócio. Repository não recebe request/response. Configuração e erros são centralizados. Blueprint category separado do report. Serviço de notificação preservado para integração opcional, sem camada pass-through artificial.

[Igualdade SHA-256 do pacote copiado](evidence/project-3-skill-hashes.json) confirma todos os arquivos canônicos idênticos na cópia. Pacote mantém referências relativas e não depende deste workspace.

## Checklist e limites

- [x] Auditoria salva antes das mudanças, revisão e waiver registrados.
- [x] Ambiente separado, baseline original e testes RED reais.
- [x] Models/Routes/Controllers, factory/config/errors e categorias separadas.
- [x] 22 métodos/caminhos preservados com sucesso autorizado e erros relevantes.
- [x] Senhas/tokens/autorização/SMTP corrigidos sem envio real.
- [x] N+1, duplicação, valores de prioridade e APIs legacy corrigidos.
- [x] Boot real, rollback, data legada copiada e preservação comprovados.
- [x] README com setup, migração/rollback e comandos reproduzíveis.

Sem requisito funcional obrigatório pendente nesta etapa. A entrega Git/commit e avaliação independente final pertencem à integração raiz. SQLite e Flask development server usados para validação local; produção requer WSGI e política de origem/configuração pelo operador. Segredos implantados anteriormente precisam rotação no ambiente real, que não foi acessado. Não se alega auditoria externa de segurança ou benchmark de capacidade.


## Verificação final de paridade

A revisão independente final identificou duas regressões de contrato e ambas receberam testes RED antes das correções. [RED busca](evidence/project-3-search-red.log): `%` deixou de funcionar porque o filtro Python substring substituíra o LIKE SQLite. [RED defaults](evidence/project-3-defaults-red.log): criação de tarefa/categoria sem description retornava null em vez de string vazia. Tokens efêmeros dos fixtures foram redigidos nestes logs.

A busca voltou a usar `.like()` parametrizado no repository, mantendo o comportamento de `%`/`_`, comparação ASCII sem distinção de caixa e comportamento Unicode próprio do SQLite. O filtro de propriedade e eager loading permanecem na mesma consulta. Testes cobrem também admin, terceiro e texto semelhante a SQL sem alteração do significado da consulta. Os defaults de criação agora são string vazia para tarefa/categoria, preservando null quando explicitamente fornecido. [GREEN focado](evidence/project-3-parity-focused.log): 2 passed; [suíte final](evidence/project-3-tests.log): **68 passed in 63.25s**. As contagens de queries permanecem 2/3/3/6, sem crescimento com os 20 registros adicionais.

No runner real, a repetição revelou uma corrida de encerramento no Windows: o launcher do virtualenv podia terminar antes do interpretador filho, deixando boot.log aberto durante limpeza do diretório temporário. O encerramento passou a usar `taskkill /PID <pid do processo próprio> /T /F` somente no Windows; POSIX mantém terminate/wait. A nova execução terminou com exit code 0 e [HTTP_MATRIX 22/22 PASS](evidence/project-3-http.log), sem traceback de limpeza. Nenhum processo alheio é encerrado. Imports comprovadamente sem uso em report_routes e serialization foram removidos; authenticate foi mantido pois user_report o utiliza.


## Correção final de codificação

A releitura final encontrou literais de erro corrompidos por leitura com encoding padrão do Windows durante a edição de paridade. Foram normalizados somente os literais afetados em validation, task_controller e repository usando leitura/escrita UTF-8 explícita. [RED exato Unicode](evidence/project-3-unicode-red.log) comprovou a divergência; [GREEN focado](evidence/project-3-unicode-green.log) observou **1 passed, 65 deselected** nas respostas JSON exatas para corpo inválido, filtro inválido e recurso ausente. Tokens efêmeros do fixture foram redigidos no RED. A busca `rg -n 'Ã|Â|�' task-manager-api --glob '*.py'` (ambientes excluídos) não encontrou fontes corrompidas após a correção. A suíte completa anterior permanece em 68 passed; o novo teste eleva a suíte coletada a 69 casos, cuja execução integral final em checkout limpo cabe à integração raiz. Não se afirma passagem de 69 antes dessa execução.

Commit das fontes refatoradas: `c700676` (conteúdo funcional validado; logs de integração posteriores identificam a revisão completa).

## Clean checkout reproduction

Revision `7100f0224a5442167cb50c2816ff5682054d0016` was cloned without existing environments; fresh pip/npm installs, all three suites and all real HTTP matrices passed. Project3 suite: 69 tests passed. [Complete reproduction log](evidence/clean-checkout-reproduction.log), [checkout/result record](evidence/clean-checkout.json), [17 validator tests](evidence/clean-validator-tests.log). The checkout remained Git-clean after execution.
