# Independent original-snapshot audits — 2026-10-22

## Execution and limits

Invoked the `refactor-arch` skill included separately in each of the three snapshots under `C:/Users/eduar/AppData/Local/Temp/refactor-final-eval-hvzb99ds`. Read each SKILL.md, the included analysis/catalog/template/MVC references and matching transformation guidance. Only these snapshots supplied project evidence. No parent documentation, prior audit, OpenSpec artifact, answer key, reference implementation, internet source, other model or subagent was consulted. The evaluator did inherit the evaluation task/context from its parent; isolation is a constrained evidence-reading protocol, not a separate sandbox or independently trained model.

Phases 1/2 only. No application imports, dependency installation, server, seed, database connection or test execution. Every behavior below is inferred from static code, not claimed as an HTTP observation. No dependency/runtime version was queried: installed versions remain unverified. The first lockfile parser call failed on its empty root key; a read-only `ConvertFrom-Json -AsHashtable` retry succeeded. Broad output truncation was resolved with focused source reads. None of those operations executed project code.

All three roots lack `.git` and any included AGENTS.md. Revision and Git dirty paths are unavailable; no ancestor Git discovery was used because it would escape the specified evidence boundary. SHA-256 manifests below identify the actual audited revision. Absence of `.git` does not justify claiming a clean Git working tree.

The skill normally forbids saving a Phase 2 report before approval. The evaluation instruction explicitly authorizes this external evidence artifact, so that narrow instruction overrides the skill's report prohibition. It does not authorize a report or any other write inside a snapshot. Destination: `D:/Docs/Workspace/mba-ia-workspace/desafios/refactor-projects-skill/reports/evidence/final-original-audits.md`. No separate post-approval project report is scheduled because approval was denied.

Skill copies: SKILL.md SHA-256 `0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115`; all seven skill files have identical relative contents across all three projects. No semantic skill version is declared. Full per-copy manifests follow.

## code-smells-project — Phase 1

Root: `C:/Users/eduar/AppData/Local/Temp/refactor-final-eval-hvzb99ds/code-smells-project`.

Stack: Python (runtime unverified), Flask declared `3.1.1`, flask-cors declared `5.0.1` (`requirements.txt:1-2`); SQLite via standard-library sqlite3 (`database.py:1,10`). Dependencies are declarations, not verified installed packages. No lockfile or tests supplied. Domain: products, customers, orders, sales and administration. Entry point `app.py`, port 5000. Lazy `get_db()` creates schema and example data in relative `loja.db`; the file is absent from the snapshot.

Source inventory: **4 Python files**: `app.py` (88 lines), `controllers.py` (292), `database.py` (86), `models.py` (314). Also inspected README and requirements; excluded those two metadata files and seven included skill files from source count. No dependencies/cache/generated/data files existed to exclude. Complete file identity inventory is in the manifest.

Current map: app registers routes but directly implements reset/SQL administration; controllers adapt HTTP, validate, perform health SQL and print notification simulations; models contain SQL plus order orchestration/report policy; database owns one mutable global connection, schema and seed. Products trace `app.py:11` → `controllers.py:5-12` → `models.py:4-22` → `database.py:7-86`. Customer login trace `app.py:21` → `controllers.py:167-186` → `models.py:105-120`. Order trace `app.py:23` → `controllers.py:188-220` → `models.py:133-169`. Sales trace `app.py:28` → `controllers.py:257-262` → `models.py:235-273`. Admin requests bypass controllers/models (`app.py:47-78`). Partial MVC exists; filename labels alone do not establish separation.

### Complete explicit HTTP inventory: 19 method/path pairs

Registration source `app.py:11-30,32,47,59`; automatic HEAD/OPTIONS excluded. Existing successful envelopes and error texts must be characterized before approved work.

| Method/path | Input and static response/effect |
| --- | --- |
| GET / | 200 message/version/endpoints object |
| GET /produtos | 200 `{dados:[product],sucesso:true}` |
| GET /produtos/busca | q/categoria/preco_min/preco_max query; 200 dados/total/sucesso; conversion errors 500 |
| GET /produtos/<int:id> | 200 dados/sucesso; 404 missing |
| POST /produtos | nome/preco/estoque required; descricao/categoria optional; validation 400; 201 dados.id/sucesso/mensagem; inserts product |
| PUT /produtos/<int:id> | same required fields, weaker validation; 404/400 or 200 sucesso/mensagem; updates product |
| DELETE /produtos/<int:id> | 404 or 200 sucesso/mensagem; hard deletes product |
| GET /usuarios | 200 dados/sucesso, including stored senha |
| GET /usuarios/<int:id> | 404 or 200 dados/sucesso, including stored senha |
| POST /usuarios | nome/email/senha; 400 or 201 dados.id/sucesso; inserts customer |
| POST /login | email/senha; 400/401 or 200 safe user subset/sucesso/mensagem; no session/token issued |
| POST /pedidos | usuario_id,itens[{produto_id,quantidade}]; 400 or 201 dados{pedido_id,total}/sucesso/mensagem; inserts order/items, reduces stock, prints notifications |
| GET /pedidos | 200 dados orders with nested items/sucesso |
| GET /pedidos/usuario/<int:usuario_id> | same envelope filtered by supplied user |
| PUT /pedidos/<int:pedido_id>/status | status enum; 400 or 200 sucesso/mensagem, including absent order; updates status, prints notification |
| GET /relatorios/vendas | 200 dados totals/discount/ticket/status counts, sucesso |
| GET /health | 200 status/database/counts/version/environment/db_path/debug/secret_key or 500 status/detalhes |
| POST /admin/reset-db | no identity/body needed; deletes four tables' rows; 200 mensagem/sucesso |
| POST /admin/query | JSON sql; empty 400; SELECT returns dados/sucesso; other SQL commits, 200 mensagem/sucesso; SQL error 500 erro |

### Phase 2 findings

Confirmed summary: **CRITICAL 3; HIGH 4; MEDIUM 3; LOW 2**. Suspicions/version-dependent issues are separate. Ranges below are relative to this project.

| ID / severity / family | Direct evidence, reachable scenario and impact | Proposed transformation / verification / dependencies / contract |
| --- | --- | --- |
| C01 CRITICAL AP-01 | `models.py:105-111,285-299,43-61,122-129,139-165`: untrusted login/search/product/customer/order values concatenate into SQL. Login email can alter predicate; search text can alter SQL. Numeric Flask path converters do not make unrelated JSON/query strings safe. | Bind all domain values; preserve LIKE wildcard semantics. Injection rejection, apostrophe round trip, correct login/search/write tests. Independent; legitimate contract preserved, injection bypass intentionally removed. Admin raw SQL is C02, not converted into a domain allowlist. |
| C02 CRITICAL AP-05 | `app.py:47-78`: unauthenticated reset and arbitrary SQL console can destroy/read/modify the entire DB. Registration and handlers have no verified upstream auth. | Verified administrator authentication/authorization; retain authorized arbitrary SQL and reset if explicitly approved as admin tools. Depends on new identity/token policy C05. Test SELECT and modifying SQL with actual effects for admin plus anonymous/user denial and reset. New 401/403 required; no silent route removal/read-only conversion. |
| C03 CRITICAL AP-02 | `models.py:72-102` serializes plaintext senha; `controllers.py:128-144` exposes list/detail without auth. Any caller retrieves all stored passwords. | Explicit safe serializer removes senha; test both endpoints with sentinel password. Coordinate C04 and C05; field removal is an explicit response contract difference. |
| C04 HIGH AP-04 | `models.py:105-111,122-130` compares/stores plaintext; `database.py:75-84` creates known example admin/customer passwords when products empty. | Salted adaptive hashes, legacy migration/reset policy, remove production auto-seeded known accounts. Test new/legacy/wrong passwords and migration persistence. Independent of C01 but combined login slice advisable; stored data changes, default account behavior changes require approval. |
| C05 HIGH AP-05 | `app.py:11-28` all CRUD, customer/order/report access has no identity; `controllers.py:195-203,237-252` trusts supplied user/status. Login returns identity JSON but establishes no credential (`167-183`). Attackers mutate stock and other customers' orders. | Approve per-route customer/owner/admin policy, signed expiring credentials and active-role lookup; restrict sensitive access. Depends on credential/config choices C04/C06; 401/403 and login token addition are differences. Test authorized success for every protected route, wrong owner, expired/tampered credentials. |
| C06 HIGH AP-02 / configuration | `app.py:7-8,88`, `controllers.py:285-289`: fixed application secret is returned by health and debug enabled on public bind. Actual session signing exploitation is unverified since no session use is present; configuration disclosure/debug exposure is confirmed. | External secret configuration, remove health secret, production debug off. Test startup config and secret-free responses/logs. Required before C05 credential signing; health field removal and startup/env behavior differences. No claim that the literal is a verified external credential. |
| C07 HIGH AP-06/AP-07 | `database.py:4-11,86`: all requests share mutable SQLite connection with thread check disabled; no teardown. `models.py:148-168` order writes have one final commit but no rollback on failure; controller catches (`218-220`) leaving pending writes that another operation can commit. This is not falsely described as multiple explicit commits in order creation. | Request-scoped connection plus explicit whole-order rollback/commit and safe stock checks. Treat C07 lifecycle/transaction as coupled scope; test parallel requests, induced second-item failure then later successful request, zero residual rows/stock drift. Failed requests cease leaving partial state; success preserved. |
| C08 MEDIUM AP-08 | `models.py:171-200,203-232`: each order performs item query, then each item performs product-name query: 1+orders+items SELECTs. `139-156` also repeats product queries per submitted item. | Bulk/join retrieval, preserving nested shape and missing-product `Desconhecido`; query-count test at 1/20 orders and orphan products. Independent or repository extraction C10; preserved. |
| C09 MEDIUM AP-09 | `controllers.py:28-54,72-90`: duplicated product validation diverges; update omits name length/category checks. `models.py:12-21,31-40,304-313`: copied product serialization. | Shared rules/serializer with create/update adapters. Test boundaries, exact envelopes and category list. Tighter update validation needs approval; extraction alone preserves current acceptance rules. Independent. |
| C10 MEDIUM AP-03 | `app.py:47-78` route SQL, `controllers.py:264-274` health SQL, `models.py:133-169,235-273` transactions/report rules mixed into persistence. Layers exist, so no fabricated single God Class finding. | Explicit product/customer/order/admin route → controller → model/repository; order service only for transaction/notification coordination. Move health queries to model. Trace imports, boot and all 19 contracts. C07 changes require joint scope if also selected; otherwise retain existing lifecycle semantics. Architecture-only behavior preserved. |
| C11 LOW AP-11 | `models.py:256-262`: unnamed discount thresholds/rates 10000/0.1,5000/0.05,1000/0.02 encode report policy. | Named descending tiers; verify below/equal/above each boundary and rounding at current return boundary. Independent; preserved. |
| C12 LOW AP-12 | `database.py:2` os import and `models.py:2` sqlite3 import have no use in all four source files (repository-wide search). | Remove unused imports; importing sqlite3 elsewhere remains necessary. Static import check plus eventual boot, no public field rename. Independent; preserved. |

Additional confirmed order-input weakness under C07/C09 scope only if explicitly selected: `models.py:139-146,163-165` accepts negative quantity and validates repeated product lines separately before decrementing, so negative values increase stock and repeated lines can oversell; no customer existence check. Approve positive integer quantities and cumulative/atomic stock constraints separately, test zero/negative/repeated lines/concurrent orders. These are business acceptance differences, not an automatic consequence of moving methods. This supplementary concern is not included as an extra counted finding.

Catalog coverage: AP-01 through AP-09 and AP-11/12 above; AP-10 no candidate requiring a confirmed deprecation in this source. No assertion of a vulnerability advisory/license finding without external dependency evidence.

### Proposed order, selectable scope, differences and rollback

First characterize 19 methods on disposable SQLite with dynamic values normalized. Select C01 independently; select credential group C03-C06 plus C02 only with explicit identity policy; select coupled C07 transaction/lifecycle; C08-C12 individually. Architecture C10 never implicitly approves security or business rule changes. No third-party package is necessarily needed for SQL binding or direct SQLite lifecycle; password/token library/runtime selection is an unresolved dependency, not authorization to install.

Explicit difference matrix: C01 domain input changes cannot alter SQL; C02 POST admin paths acquire 401/403 while preserving admin SQL/reset success; C03 GET usuarios list/detail lose senha; C04 POST usuarios/login password storage/migration and automatic example accounts change; C05 all protected product writes/customer reads/order/report paths acquire identity/owner checks and login gains verifiable credential; C06 GET health loses secret_key and debug startup config changes; C07 POST pedidos failure leaves no pending state; optional quantity corrections reject previously accepted invalid orders; C09 PUT produtos rejects invalid name/category only if selected. Everything else preserves method/path/status/envelopes and business values. Tests named per finding are required for these differences.

Before approved data changes: backup existing loja.db, rehearse non-destructive hash migration on a copy, decide legacy-login upgrade vs forced reset and retain legitimate customer/order/product IDs. Never run reset/seed as a migration. Roll back each independently committed code slice; restore DB backup only under planned downtime/data reconciliation because post-migration writes may otherwise be lost. Arbitrary SQL console approval must explicitly accept its exceptional admin trust boundary.

Approval surface that would ordinarily be presented: “Quais IDs C01–C12 e quais diferenças de contrato acima você aprova? Para C02/C05, aprove também a política de identidade/permissões; C07 requer o grupo de conexão/transação.” This is recorded, not sent as a new question: the supplied answer is **“Não autorizo alterações.”** Phase 3 refused; no changes authorized.

## ecommerce-api-legacy — Phase 1

Root: `C:/Users/eduar/AppData/Local/Temp/refactor-final-eval-hvzb99ds/ecommerce-api-legacy`.

Stack: JavaScript/CommonJS, Node runtime unverified; Express declared `^4.18.2` and sqlite3 `^5.1.6` (`package.json:9-11`), lockfile resolved `4.22.1` and `5.1.7`. Lock resolutions are static evidence, not installed-version verification. Domain is LMS courses/users/enrollments/payments despite project name. Persistent storage is SQLite `:memory:` (`src/AppManager.js:7`), reset on every process restart, schema/seeds during boot. Entry point/start command `src/app.js`/`node src/app.js`; only start script exists, no supplied tests.

Source inventory **3 JavaScript files**: `src/app.js` (14 lines), `src/AppManager.js` (141), `src/utils.js` (25). Other analyzed files package.json/package-lock.json/api.http/README excluded from source count, as are seven skill files. No dependency/data/cache trees supplied.

Current map: startup composes manager then listens; AppManager owns connection/schema/seeds, route registration, validation, account creation, payment simulation, enrollment writes, financial aggregation and deletion. utils mixes config, cache, weak password encoding. Checkout trace `src/app.js:8-10` → `src/AppManager.js:28-78` → same object's SQLite callbacks plus `utils.js:17-22`/logAndCache. Financial domain trace `AppManager.js:80-129` queries courses, enrollments, users/payments and builds response in same handler. User deletion `131-137` directly issues SQL. No separate Model/View-Route/Controller boundaries.

### Complete explicit HTTP inventory: 3 pairs

| Method/path / registration source | Input and existing static response/effect |
| --- | --- |
| POST /api/checkout — `src/AppManager.js:28` | JSON usr/eml/pwd/c_id/card; usr/eml/c_id/card truthy required (pwd defaults); 400 plain Bad Request/payment refused, 404 course absent, 500 plain DB/enrollment/payment error, 200 JSON msg/enrollment_id; may create account then enrollment/payment/audit and cache |
| GET /api/admin/financial-report — `:80` | 200 JSON array [{course,revenue,students:[{student,paid}]}], empty []; initial query error 500 plain Erro DB; nested errors mishandled |
| DELETE /api/users/:id — `:131` | 200 plain deletion message including orphan warning, regardless absent user/SQL failure; deletes only users |

### Phase 2 findings

Confirmed summary: **CRITICAL 0; HIGH 6; MEDIUM 1; LOW 2**. Placeholder-looking keys are not counted as verified usable production secrets.

| ID / severity / family | Direct evidence, reachable scenario and impact | Transformation / verification / dependencies / contract |
| --- | --- | --- |
| E01 HIGH AP-03 | `src/AppManager.js:4-137` combines five domain tables/schema/seed/HTTP/payment/logging/cache/report and deletion; unrelated responsibilities confirmed, not merely class length. | Separate composition, routes, controllers and repositories; transactional checkout service meaningful, payment/log integration adapters. All 3 endpoint characterization, import/SQL boundary tracing. Independent architecture scope cannot imply E02-E07; preserved. |
| E02 HIGH AP-04 | `src/utils.js:17-22` hashes only repeated first two base64 characters, yielding deterministic collisions/reversibility rather than secure hashing; `AppManager.js:18,68-69` plaintext seeded credential and default password. | Runtime-compatible salted adaptive hashing, explicit legacy reset/upgrade plan. Test distinct/same-prefix passwords, salts and default handling. New auth E03 needs a credential policy; no current login method to silently repurpose. Stored values/default account policy change. |
| E03 HIGH AP-05 | `AppManager.js:80-137` admin report and delete have no authentication; checkout `40,66-75` selects existing user by submitted email and never verifies pwd. A caller can enroll as another user and delete users. | Establish verified identity/role, owner policy and checkout identity binding. Depends on E02 and secure configured credential mechanism; approval must select how credentials are obtained since no login route currently exists. 401/403 and credential acquisition are differences; test real authorized checkout/report/delete and denials. |
| E04 HIGH AP-07 | `AppManager.js:50-71` account inserted before payment refusal, enrollment/payment/audit individually autocommit with no BEGIN/ROLLBACK. Payment insert failure leaves enrollment; audit error ignored (`57-60`) returns success. | Whole checkout transaction including newly created account, enrollment, payment, audit; validate simulated payment before writes; serialize complete transactions on the single Node connection. Test denied new-account checkout leaves nothing, induced payment/audit error rollback, successful four-table effects and concurrency. Coupled transaction scheduling needed, not a connection-per-request :memory: rewrite. Failure effects change; success preserved. |
| E05 HIGH AP-07 / integrity | `AppManager.js:12-16,131-136` no FK constraints and user delete leaves enrollments/payments, reports fall back Unknown. Delete also ignores DB failure. | Approve retention policy: soft delete/anonymize, restrict or atomic cascade. Never infer cascade from smell. Test existing/absent user, SQL error and downstream report/financial retention. Depends on policy and schema migration; deletion body/status/effects may change, explicitly unresolved. |
| E06 HIGH AP-02 | `AppManager.js:45` logs the full submitted card plus configured paymentGatewayKey on every payment attempt. Sensitive card logging is confirmed even if key is illustrative. | Stop logging card/key; external config where needed; sentinel secret/card log assertion. No HTTP change; logs intentionally redact sensitive content. Independent. |
| E07 MEDIUM AP-08 / errors | `AppManager.js:83-126`: 1+courses+2*enrollments queries. Nested enrollment errors dereference undefined (`92-93`); callback errors ignored in user/payment queries. | Set-based/bulk report repositories, explicit error forwarding/middleware, preserve courses with zero enrollments and Unknown user/zero payment semantics; avoid multiplying revenue with multiple payment rows. Query-count 1/20 fixtures plus DB error response, all envelopes. Dependency E01 only if extraction selected; error path becomes reliable 500 instead of thrown/hung behavior, difference. |
| E08 LOW AP-12 | `AppManager.js:2,29-33` unused imported totalRevenue and opaque internal u/e/p/cid/cc; `utils.js:10,25` totalRevenue is exported zero with no caller use anywhere in three files. | Remove unused local import; rename internals, retain public usr/eml/pwd/c_id/card. Export removal requires external consumer decision (none supplied), not claimed globally safe. Boot/mapping tests; independent; preserved public HTTP. |
| E09 LOW AP-11 | `AppManager.js:46,68` unnamed payment prefix rule/default password and `utils.js:19-22` repeated encoding literals. Password constants alone do not fix E02. | Name approved simulation policy, keep startsWith("4") behavior and defaults unless E02 selected. Boundary/card fixture tests; independent naming slice preserves behavior. |

Suspicions/limits: `utils.js:1-6` credential-looking config values may be examples; dbUser/dbPass/smtpUser have no consuming DB/SMTP integrations, so no confirmed usable external credential or fabricated CRITICAL secret count. `src/app.js:9-12`, `AppManager.js:10-22` do not await database readiness or handle init errors; statements are queued by serialize before routes listen, so a reproducible request-before-schema race is **unverified**, not asserted. Propose explicit readiness and boot-failure test if selected. `utils.js:9-14` cache grows with successful distinct users, but memory exhaustion impact is unmeasured. AP-01 no confirmed SQL injection: request values use placeholders. AP-06 one Node SQLite handle alone is not unsafe request lifecycle evidence; complete transaction serialization is specifically an E04 dependency. AP-09 no sufficient divergent duplicate rule/serializer evidence; AP-10 no confirmed applicable deprecation. All catalog families inspected without forcing counts.

### Plan, differences and approval surface

Characterize 3 methods first using isolated process/memory DB; keep deterministic payment simulation, no external charging. E01 can be architecture-only; E02+E03 form a credential/auth group; E04 includes whole-transaction scheduling; E05 is separate data-retention approval; E06-E09 independently selectable. No third-party installation authorized; secure password/credential implementation dependencies must be selected based on runtime and approved identity design.

Difference matrix: POST checkout E02 changes password representation/default policy; E03 binds existing-user checkout to verified identity and introduces denials/credential provision; E04 denied/failed attempts leave no new account/enrollment/payment/audit; E06 logs omit cards/key; GET report E03 adds authorization, E07 replaces crash/hang with defined 500; DELETE users E03 adds authorization, E05 retention/missing/error status/body/effects depend on explicit choice. Existing successful routes and fields remain; no API request-key renames. Financial semantics require preserving per-enrollment paid amount selection or explicitly agreeing a change for multiple payments; bulk JOIN cannot silently sum every row.

Current memory data is ephemeral; switching to persistent SQLite is a contract/operations change and not proposed implicitly. For a future persistent deployment, backup and migration rehearsal precede schema/password/retention changes. Rollback code slices independently; E02/E05 schema/credential changes require versioned reversible migration or planned restore with reconciliation. Never run seed as migration.

Recorded approval surface: “Quais IDs E01–E09 e diferenças você aprova? E03 requer política de identidade e obtenção de credenciais; E04 inclui conta/auditoria/transação completa; E05 exige decisão de retenção.” Supplied response **“Não autorizo alterações.”** Phase 3 refused; no scope approved.

## task-manager-api — Phase 1

Root: `C:/Users/eduar/AppData/Local/Temp/refactor-final-eval-hvzb99ds/task-manager-api`.

Stack: Python runtime unverified; requirements declare Flask 3.0.0, Flask-SQLAlchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0, python-dotenv 1.0.0. No lockfile, installed versions unverified; SQLAlchemy underlying release not pinned. ORM extension uses scoped session, not evidence of the direct-SQL global connection anti-pattern. SQLite URI `sqlite:///tasks.db` (`app.py:11`), actual resolved storage path unverified without application context; no DB supplied. Entry `app.py`, initializes schema during import (`30-31`) and listens debug on all interfaces (`34`). `seed.py:11-14` deletes tasks/users/categories and commits before repopulation: destructive, never executed.

Source inventory **15 Python files** including four package initializers: `app.py`, `database.py`, `seed.py`, `models/{__init__,category,task,user}.py`, `routes/{__init__,report_routes,task_routes,user_routes}.py`, `services/{__init__,notification_service}.py`, `utils/{__init__,helpers}.py`. README/requirements and seven skill files excluded from source count. No tests/dependency caches/generated/data trees supplied.

Current map: blueprints/models/services directories exist; routes still own query/transaction/validation/report orchestration and serialization. No explicit controller boundary. `database.py` is appropriate extension composition, models have useful mappings/domain methods, NotificationService has no in-project caller. Task trace `app.py:18` → `routes/task_routes.py:85-154` → Task/User/Category queries → db.session add/commit; user trace `app.py:19` → `routes/user_routes.py:42-90` → User.set_password/to_dict and session; reporting/categories trace `app.py:20` → `routes/report_routes.py:12-223` → ORM queries/loops/commit. Keep useful mappings/blueprints rather than replacing the stack.

### Complete explicit HTTP inventory: 22 pairs

No blueprint prefixes (`app.py:18-20`). Automatic HEAD/OPTIONS excluded. Default decorators `app.py:22,26` imply GET.

| Method/path / registration line | Input and existing static response/effect |
| --- | --- |
| GET / — app.py:26 | 200 message/version |
| GET /health — app.py:22 | 200 status/timestamp |
| GET /tasks — routes/task_routes.py:11 | 200 task array incl overdue/user_name/category_name, 500 generic on caught error |
| GET /tasks/<int:task_id> — :65 | 200 task dict + overdue or 404 |
| POST /tasks — :85 | title required, optional description/status/priority/user_id/category_id/due_date/tags; 400 validation/404 relation; 201 task.to_dict; persists task |
| PUT /tasks/<int:task_id> — :156 | partial fields, omitted preserved, falsey due_date clears; 400/404 or 200 task dict; persists update |
| DELETE /tasks/<int:task_id> — :225 | 404 or 200 message; deletes task, 500 rollback |
| GET /tasks/search — :240 | q/status/priority/user_id query; 200 plain task.to_dict array; invalid integer unhandled |
| GET /tasks/stats — :273 | 200 total/status/overdue/completion_rate object |
| GET /users — routes/user_routes.py:10 | 200 safe user subset + task_count array |
| GET /users/<int:user_id> — :27 | 404 or 200 user dict including password hash and tasks array |
| POST /users — :42 | name/email/password/optional role; 400 validation/409 duplicate, 201 user dict including hash; accepts admin role |
| PUT /users/<int:user_id> — :92 | partial name/email/password/role/active; 400/404/409 or 200 user dict including hash |
| DELETE /users/<int:user_id> — :134 | 404 or 200 message; deletes user's tasks then user atomically, rollback on failure |
| GET /users/<int:user_id>/tasks — :153 | 404 or 200 task subset array with overdue |
| POST /login — :185 | email/password; 400/401/403 inactive or 200 message/user including hash/token fake-jwt-token-ID |
| GET /reports/summary — routes/report_routes.py:12 | 200 generated_at/overview/tasks_by_status/tasks_by_priority/overdue/recent_activity/user_productivity |
| GET /reports/user/<int:user_id> — :103 | 404 or 200 user subset/statistics |
| GET /categories — :157 | 200 category array + task_count |
| POST /categories — :167 | name required; description/color optional; 400 or 201 category; persists |
| PUT /categories/<int:cat_id> — :190 | partial name/description/color; 404 or 200 category; nullable/malformed JSON unhandled before commit try |
| DELETE /categories/<int:cat_id> — :211 | 404 or 200 message; delete category, 500 on commit failure; task reference policy not explicit |

### Phase 2 findings

Confirmed summary: **CRITICAL 1; HIGH 2; MEDIUM 4; LOW 2**. Other unverified/deprecation observations do not inflate totals.

| ID / severity / family | Evidence, reachable scenario and impact | Transformation / verification / dependencies / contract |
| --- | --- | --- |
| T01 CRITICAL AP-05 | `routes/user_routes.py:42-86,92-129,134-148` anonymous clients set admin role/active/password and delete users plus tasks. All route registrations have no auth middleware; task/report/category reads/writes likewise unguarded. Admin-like role is not itself authorization. | Approve role/owner matrix, verified identity and active-role lookup; restrict role/active changes and deletes, bind ownership of tasks. Depends on T03 secure credential/config policy; test authenticated success for each protected method plus anonymous/user/wrong-owner/tampered/expired cases. New 401/403 and prohibited self-elevation are explicit differences. |
| T02 HIGH AP-02 | `models/user.py:16-24` includes password; `routes/user_routes.py:33-40,85-86,129,207-210` expose hash in detail/create/update/login. List endpoint already omits password; do not invent list hash leak. | Explicit safe user serializer, preserving route-specific fields/tasks. Sentinel hash absence tests on four affected routes. Independent from T03 but coherent credential slice; password field removed from those contracts. |
| T03 HIGH AP-04 | `models/user.py:27-32` fast unsalted MD5; `routes/user_routes.py:207-211` predictable fake token without signature/expiry, and no verifier. No evidence any handler currently trusts this fake token. | Salted adaptive hashes, explicit legacy MD5 migration/reset, signed expiring token + verifier for T01. Config key from env, not `app.py:13` literal. Tests unique salts, legacy persisted upgrade, wrong/tampered/expired/inactive cases. T01 depends on verifier; token format changes and legacy policy require approval. |
| T04 MEDIUM AP-03 | `routes/task_routes.py:85-154,156-223`, `routes/user_routes.py:42-90,134-151`, `routes/report_routes.py:12-101,167-223`: handlers own validation, ORM details, transactions and aggregation; useful entities/blueprints already exist. | Keep Views/Routes request mapping, add explicit Controllers for use cases; models/repositories own querying; report orchestration service meaningful, no generic pass-through services. Trace each domain, verify no model imports HTTP, all 22 contracts. Independently selectable architecture-only; no automatic T01-T03 scope. |
| T05 MEDIUM AP-08 | `routes/task_routes.py:14-57` queries user/category per task (identity-map caching may reduce duplicates, not distinct-ID growth); `routes/user_routes.py:12-22` lazy u.tasks per user; `routes/report_routes.py:53-67,157-164` per-user task queries and per-category counts. | Eager/bulk retrieval and grouped counts, preserving None/empty relations and all response fields. Query-count test distinct related users/categories at 1/20 rows. Independent or alongside T04; preserved. Summary fixed count queries alone are not N+1. |
| T06 MEDIUM AP-09 | `routes/task_routes.py:17-39,69-80,96-114,166-184`, `models/task.py:23-60`, `routes/user_routes.py:162-180`, `routes/report_routes.py:33-43,132-135`: repeated task serialization/status/priority/overdue rules; helpers duplicate rules but are unused (`utils/helpers.py:57-108`). | Share domain predicates/validators and serializers with explicit list/detail/user-task variants. Do not directly replace all responses with to_dict: list adds names/overdue, user-task is subset. Test schema-specific exact fields, omitted partial update fields, 2/3/200/201 titles and date edges. Independent; stricter type validation/trim/date format differences separate approval. |
| T07 MEDIUM input/error handling | `routes/task_routes.py:96-114,167-183,260-264`, `routes/user_routes.py:61,64,106,115`, `routes/report_routes.py:196-202`: type-dependent len/comparison/regex/int operations outside controlled error mapping. Invalid JSON field types/query integers can yield 500 instead of validation responses. | Validate input types before domain operations; centralized consistent error adapter. T06 shared validators may implement but require joint selected scope. Table-driven malformed numeric/title/email/date/JSON cases. Invalid inputs intentionally become specified 400; legitimate success envelopes preserved. |
| T08 LOW AP-11 | `routes/task_routes.py:96-114,167-183`, `routes/user_routes.py:64,115`, `utils/helpers.py:110-116`: repeated domain thresholds/status/role/priority values ignore existing constants. | Name/use approved domain constants while preserving minimum password 4, priority 1..5 and title 3..200 unless policy separately changed. Boundary tests; T06 dependency only if reuse integrated. Preserved values. |
| T09 LOW AP-12 | `app.py:7` unused os/sys/json; `routes/task_routes.py:7` json/os/sys/time unused; `routes/report_routes.py:7-8` imported format_date/calculate_percentage/json unused; `models/task.py:3` unused json; search shows NotificationService never called and process_task_data never used. | Remove proven unused local imports; review whether uncalled service/helper exports should be retained as public extension points. No automatic SMTP integration or deletion of public helpers. Static usage check plus boot; independent; HTTP preserved. |

Unverified/separate observations: `app.py:13` fixed SECRET_KEY and `services/notification_service.py:7-19` SMTP credential literal; secret signing not used yet, NotificationService has no callers, and credential usability unverified, so no fabricated confirmed CRITICAL external-secret finding. External config is a T03 prerequisite if signing is added. `app.py:34` public debug is a confirmed unsafe production deployment choice; production debug-off changes startup behavior, include as an explicit optional configuration scope, not proof deployed internet exposure. `seed.py:11-14,37,63,92` destructive multi-commit reseed is an operational hazard; caller authorization and backup required, never used as audit/testing shortcut. Import-time schema creation `app.py:30-31` is why no app import was run.

AP-10 candidate `Query.get()` at `routes/task_routes.py:42,51,67,117,122,158,188,195,227`, `routes/user_routes.py:29,94,136,155`, `routes/report_routes.py:105,192,213`; datetime.utcnow across models/routes/helpers/seed. **Deprecation status unverified**, not a confirmed finding: supplied manifests do not pin actual SQLAlchemy/Python runtime and official documentation was intentionally not fetched under evidence-isolation constraints. Embedded playbook names the official documentation URLs but a skill example is not runtime verification. In a later authorized investigation confirm runtime/version and official applicability before replacement, preserving naive-UTC storage/string formats or separately approving aware UTC migration.

AP-01 no confirmed SQL injection: ORM like(f'%{query}%') builds bound expressions, not raw SQL. AP-06 db=SQLAlchemy() is scoped extension, not the unsafe global sqlite connection pattern. AP-07 user deletion does have one commit plus rollback, so no manufactured partial-commit finding. Category deletion's referential effects require ORM/database verification before labeling a specific outcome. All 12 catalog families inspected.

### Plan, differences and approval surface

First characterize all 22 method/path pairs on disposable SQLite, including naive dates and response-specific fields. T04 architecture-only independently; T02 independent safe serialization; T01+T03 identity/auth group requires configuration and credential migration policy; T05 query shape independent; T06/T08 extraction independent if behavior retained; T07 type-validation differences require selection. T09 local dead imports independently. New dependencies not required merely to organize MVC; choose compatible password/token implementations only with approved runtime evidence. marshmallow is declared but unused, which is not authority to introduce changed validation semantics or remove requirements packages.

Difference matrix: T01 protected tasks/users/reports/categories routes receive identity/role/owner checks and 401/403, POST/PUT users stop anonymous role escalation; T02 GET users/id, POST users, PUT users/id and POST login lose password hash field; T03 POST login token changes from fake string to signed expiring value, password storage/migration changes; T07 malformed JSON/types/query ints become defined 400; optional production debug config changes boot behavior. T04/T05/T06/T08/T09 otherwise preserve route/status/response/side effects, including user deletion's task cascade and category policy until explicitly decided. Broader password-length, title trimming, date-format/timezone, pagination, SMTP notification activation and retention changes are **not** implied.

Backup actual resolved tasks.db before any approved migration, rehearse legacy MD5 strategy on a copy, preserve IDs/relations, never execute destructive seed against existing data. Rollback each code slice; upgraded hashes and new tokens require compatible transition/rotation or planned restore/reconciliation, not blind downgrade. Do not claim existing data needs timezone conversion until runtime/storage contract is verified.

Recorded approval surface: “Quais IDs T01–T09 e diferenças você aprova? T01 exige T03 e política explícita de papéis/propriedade/migração; T07 altera respostas para entradas inválidas.” Supplied answer **“Não autorizo alterações.”** Phase 3 refused; no scope approved.

## Observed evaluation outcome

The same skill identified three distinct architectures from direct evidence, enumerated **19/3/22 = 44** explicit HTTP pairs and **4/3/15 = 22** source files, preserved the already useful ORM/blueprint components, treated the Node checkout's new account and audit row as part of transaction scope, and kept arbitrary admin SQL as an authorization-boundary decision. It did not assert ORM interpolation was SQL injection, Node's single SQLite handle was automatically unsafe, or unavailable runtime evidence proved deprecation. These are observations of this evaluator's static invocation, not evidence of Phase 3 implementation quality or fresh-process reproducibility. No minimum finding target or manual answer key was used.

**Final gate: “Não autorizo alterações.” I refuse to start Phase 3.** No findings were corrected, no runtime acceptance criteria were executed, and all findings remain unresolved proposals. The evaluation ends at refusal. Before/after file-content verification follows; it cannot prove access timestamps, permissions, empty-directory identity or transient writes by unrelated processes, but it covers every supplied regular file plus additions/deletions by comparing path sets.
## Complete before/after manifest

PowerShell Get-FileHash SHA256, recursive regular files including hidden entries; path set and byte lengths compared as well as SHA256. **PASS: all 51 paths/content hashes/byte lengths identical; 0 added, 0 removed, 0 changed**. Per project: code-smells-project 13 files, ecommerce-api-legacy 14, task-manager-api 24. Skill manifest is included per project, not inferred from one copy. Before capture preceded all project-source inspection; after capture followed the denial and audit. Hashes concern snapshot files, not this separately authorized report.

| Snapshot-relative path | Bytes before/after | SHA256 before | SHA256 after |
| --- | --- | --- | --- |
+| code-smells-project/.agents/skills/refactor-arch/references/anti-patterns.md | 2615 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 |
| code-smells-project/.agents/skills/refactor-arch/references/audit-report-template.md | 1278 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 |
| code-smells-project/.agents/skills/refactor-arch/references/mvc-guidelines.md | 1560 | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D |
| code-smells-project/.agents/skills/refactor-arch/references/project-analysis.md | 2143 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 |
| code-smells-project/.agents/skills/refactor-arch/references/refactoring-playbook.md | 13092 | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF |
| code-smells-project/.agents/skills/refactor-arch/references/validation.md | 1376 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 |
| code-smells-project/.agents/skills/refactor-arch/SKILL.md | 5257 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 |
| code-smells-project/app.py | 3674 | B106B109BF2D2114A23CFA2BE91F4654781A75239350FC64844217BA7E394EE6 | B106B109BF2D2114A23CFA2BE91F4654781A75239350FC64844217BA7E394EE6 |
| code-smells-project/controllers.py | 10377 | EDFF36072F19B4B8E471BF6AA35CCA0FFAA09495636A7D9BCC807447BB7EEFD6 | EDFF36072F19B4B8E471BF6AA35CCA0FFAA09495636A7D9BCC807447BB7EEFD6 |
| code-smells-project/database.py | 3448 | 2327FD05C963F243C86182287141D264F2960FF8C8A3512CB95EF13CF91FD4D7 | 2327FD05C963F243C86182287141D264F2960FF8C8A3512CB95EF13CF91FD4D7 |
| code-smells-project/models.py | 10073 | 6ADE3BCA1638A7A3A26C565D3DD34F0EB4F34DB2615E57315BB5373C4789F111 | 6ADE3BCA1638A7A3A26C565D3DD34F0EB4F34DB2615E57315BB5373C4789F111 |
| code-smells-project/README.md | 350 | EE80EDCE8779DC0727330C980E54B6DDBE11547AE5AE5C8571A655147BC44249 | EE80EDCE8779DC0727330C980E54B6DDBE11547AE5AE5C8571A655147BC44249 |
| code-smells-project/requirements.txt | 33 | 9920665BD7C8D475DEE2EEE94465F9F02B2ECD834B1975A058A0206CD91CDDE4 | 9920665BD7C8D475DEE2EEE94465F9F02B2ECD834B1975A058A0206CD91CDDE4 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/anti-patterns.md | 2615 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/audit-report-template.md | 1278 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/mvc-guidelines.md | 1560 | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/project-analysis.md | 2143 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/refactoring-playbook.md | 13092 | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/validation.md | 1376 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/SKILL.md | 5257 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 |
| ecommerce-api-legacy/api.http | 616 | 48D118298DB6167B494AE20D87A0DDFDB0E60812AA198E4D746A5971F4B36E39 | 48D118298DB6167B494AE20D87A0DDFDB0E60812AA198E4D746A5971F4B36E39 |
| ecommerce-api-legacy/package-lock.json | 85218 | 82AC34E44F3A7C82893CDB99715FA851E3D66F6342FBB15C406A2A20C20C303A | 82AC34E44F3A7C82893CDB99715FA851E3D66F6342FBB15C406A2A20C20C303A |
| ecommerce-api-legacy/package.json | 304 | 58A14B9AB83C508A285ABBCC1787D64090534502BBF2D3EDA12053EB24E78D90 | 58A14B9AB83C508A285ABBCC1787D64090534502BBF2D3EDA12053EB24E78D90 |
| ecommerce-api-legacy/README.md | 358 | E239A8B5DC4B1C413BA21ADD9869695A4AC7D43E2AB73E499C1A1D688DE5EA81 | E239A8B5DC4B1C413BA21ADD9869695A4AC7D43E2AB73E499C1A1D688DE5EA81 |
| ecommerce-api-legacy/src/app.js | 370 | BF2C87F0AD5604772058C5A9CB758841D2DF5C314B7B644BBF4A3C8C75474FC3 | BF2C87F0AD5604772058C5A9CB758841D2DF5C314B7B644BBF4A3C8C75474FC3 |
| ecommerce-api-legacy/src/AppManager.js | 6847 | 5906937CFD56420A25B42ABCEAD09F520BBF133030C7B1F816B0B374501CEA36 | 5906937CFD56420A25B42ABCEAD09F520BBF133030C7B1F816B0B374501CEA36 |
| ecommerce-api-legacy/src/utils.js | 665 | 0739B7FACD3BDEE5CB0E70C0E8FC00B220A2D9151C0CEF9512D1A26D994A4390 | 0739B7FACD3BDEE5CB0E70C0E8FC00B220A2D9151C0CEF9512D1A26D994A4390 |
| task-manager-api/.agents/skills/refactor-arch/references/anti-patterns.md | 2615 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 |
| task-manager-api/.agents/skills/refactor-arch/references/audit-report-template.md | 1278 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 |
| task-manager-api/.agents/skills/refactor-arch/references/mvc-guidelines.md | 1560 | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D |
| task-manager-api/.agents/skills/refactor-arch/references/project-analysis.md | 2143 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 |
| task-manager-api/.agents/skills/refactor-arch/references/refactoring-playbook.md | 13092 | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF |
| task-manager-api/.agents/skills/refactor-arch/references/validation.md | 1376 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 |
| task-manager-api/.agents/skills/refactor-arch/SKILL.md | 5257 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 |
| task-manager-api/app.py | 900 | A28AC584FB04B9A74D193E812DFED9E8178A4546F3AFD8755D4FDC72A7E797FA | A28AC584FB04B9A74D193E812DFED9E8178A4546F3AFD8755D4FDC72A7E797FA |
| task-manager-api/database.py | 62 | 5F9AB7B94BDECC149AE3BB18BA50D60B07462C4C41A3A18809ADFD43F089A89C | 5F9AB7B94BDECC149AE3BB18BA50D60B07462C4C41A3A18809ADFD43F089A89C |
| task-manager-api/models/__init__.py | 98 | 89D61649A4486EC71BBF6292B34A39BF204490005A0672D9BD6329ECBA2CB1ED | 89D61649A4486EC71BBF6292B34A39BF204490005A0672D9BD6329ECBA2CB1ED |
| task-manager-api/models/category.py | 666 | 8DF4C96DFCB1B3AA6BE86FFAE32168AEEC431F58927622490E744AF449B0D1F4 | 8DF4C96DFCB1B3AA6BE86FFAE32168AEEC431F58927622490E744AF449B0D1F4 |
| task-manager-api/models/task.py | 2216 | EB120E934F34488DD1CC1FD40A41E31D4FB2C0A0E4BA8D9E4C70C7D90F9C0A04 | EB120E934F34488DD1CC1FD40A41E31D4FB2C0A0E4BA8D9E4C70C7D90F9C0A04 |
| task-manager-api/models/user.py | 1169 | E689D4337DAD4C4327A58327718687A46EF49C0EE934FAFB109DAB51CE4667EC | E689D4337DAD4C4327A58327718687A46EF49C0EE934FAFB109DAB51CE4667EC |
| task-manager-api/README.md | 624 | E67EBF77375CF0E8A535389A077B0AC80353D6378276F0942576D3A911944F37 | E67EBF77375CF0E8A535389A077B0AC80353D6378276F0942576D3A911944F37 |
| task-manager-api/requirements.txt | 119 | C56CBF059924E9A56AE63017CAC7861DED0CFBDEE88792D59D0B8F99BD789F00 | C56CBF059924E9A56AE63017CAC7861DED0CFBDEE88792D59D0B8F99BD789F00 |
| task-manager-api/routes/__init__.py | 2 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 |
| task-manager-api/routes/report_routes.py | 7096 | 2A5F9FA1A15A3E1520E4E8ED722F83EF233A261A40C15B0F057C4AE3679BD341 | 2A5F9FA1A15A3E1520E4E8ED722F83EF233A261A40C15B0F057C4AE3679BD341 |
| task-manager-api/routes/task_routes.py | 9772 | 3E7AE78B93F29BAEF102D1FF5A74D3DABE39C827C6A6A33C1DFF2098C46CF89B | 3E7AE78B93F29BAEF102D1FF5A74D3DABE39C827C6A6A33C1DFF2098C46CF89B |
| task-manager-api/routes/user_routes.py | 6666 | FFB128DB5F89A8276CF1561D6D529D377127C6A331C7BF263361126EED46A20C | FFB128DB5F89A8276CF1561D6D529D377127C6A331C7BF263361126EED46A20C |
| task-manager-api/seed.py | 4588 | 57986FDF9DFA0B47EDB40F0919F0F6D4C1AB5C4BC2FB72689176262CB34881C6 | 57986FDF9DFA0B47EDB40F0919F0F6D4C1AB5C4BC2FB72689176262CB34881C6 |
| task-manager-api/services/__init__.py | 2 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 |
| task-manager-api/services/notification_service.py | 1817 | 1C5F6B74CD562EB5A6E8C06B66C836BA7692ADE1AA15C04D44FFA331FDEA34E8 | 1C5F6B74CD562EB5A6E8C06B66C836BA7692ADE1AA15C04D44FFA331FDEA34E8 |
| task-manager-api/utils/__init__.py | 2 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 |
| task-manager-api/utils/helpers.py | 2978 | 62F0E0A67F873022741BDE69888AC66DA0EC9397010C254CE83446D6D52F1810 | 62F0E0A67F873022741BDE69888AC66DA0EC9397010C254CE83446D6D52F1810 |
