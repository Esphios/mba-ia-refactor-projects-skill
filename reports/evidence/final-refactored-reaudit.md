# Refactored-project read-only re-audit — 2026-10-22

## Scope, independence and state

This is a second actual application of the included `refactor-arch` skill to the current three projects under `D:/Docs/Workspace/mba-ia-workspace/desafios/refactor-projects-skill`. I read each local SKILL.md, analysis/catalog/template/MVC/validation guidance, relevant playbook guidance and the current application source, configuration/manifests and local README. No root manual answer key, OpenSpec, existing audit, reference implementation, test contents or runtime evidence logs were read. README links to outer reports were not followed. Only Git revision/status metadata was queried outside regular source reads.

The same evaluator previously audited original snapshots and retains that context. Contract comparisons below therefore use remembered original source evidence, not a new blind independent model run. Source-state comparisons are independent SHA-256 measurements, not model-independent audit proof. Parent implementation context and messages identify concurrent corrections and their reported test-log paths; those reported runtime results are clearly separated from my own static observations. This audit does not demonstrate repeated-run determinism across fresh agents.

No application imports, installs, database operations, server startup, seed, tests or application mutations were performed by this evaluator. Shell reads, `rg`, Git read-only metadata and SHA-256 only. An initial PowerShell pipeline syntax error was corrected; a broad recursive hash enumeration exceeded the synchronous tool interval, so the complete stored baseline was recollected using scoped `rg --files` excluding dependency/generated/test trees. Neither operation executed project code. The outer evidence report is explicitly authorized by the evaluation task, overriding the skill's normal prohibition on saving a preapproval Phase 2 report only for this artifact.

All three projects inherit Git HEAD `6d1ce6248c3e956801010a89d8bdaab48029bf30`; all have substantial dirty worktrees with modified README/entry/source, removed legacy modules, and untracked new MVC/auth/config/tests/skill files. HEAD alone does not identify audited code; manifests below identify source contents. No project-local AGENTS.md was found. The root Git metadata is shared; this audit did not inspect ancestor instruction/manual files. The analysis boundary was explicitly supplied by the parent task.

Skill SHA-256 in each project: `0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115`. All seven relative skill files match across copies. No semantic skill version is declared.

| Project | Application source count | Explicit HTTP pairs | Declared/resolved dependency evidence | Runtime confidence |
| --- | --- | --- | --- | --- |
| code-smells-project | 30 Python files, including package initializers | 19 | requirements: Flask 3.1.1, flask-cors 5.0.1; dev pytest 8.4.2 | Python/installed packages unverified by this audit |
| ecommerce-api-legacy | 24 JavaScript files under src | 4 (original 3 plus login) | package: Express ^4.18.2, sqlite3 ^6.0.1, Node >=20.17.0; lock: Express 4.22.3, sqlite3 6.0.1 | Node/installed modules unverified; README recommends Node24 |
| task-manager-api | 29 Python files, including package initializers | 22 | Flask3.0.0, Flask-SQLAlchemy3.1.1, flask-cors4.0.0, marshmallow3.20.1, requests2.31.0, python-dotenv1.0.0; dev pytest8.3.5 | README claims Python3.12.10/SQLAlchemy2.1.6 verified elsewhere; not independently queried here |

Counts exclude tests/test, `.venv`, node_modules, caches, generated/instance/local databases, skill Markdown, README and manifests. No test contents or report contents were inspected. Baseline identity manifest includes 116 regular source/support/skill files (41/36/39), including README/manifests/examples; it does not cover ignored/generated/excluded trees. Source inventory is completely enumerated by the manifest's `.py`/`.js` entries.

## code-smells-project

### Phase 1: responsibility and dependency trace

Flask app factory `app.py:12-24` configures extensions/error mapping/blueprints; DB initialization is explicit CLI by default (`config.py:11-12`, `database.py:116-138`). Direct SQLite uses request/app-context scoped connection (`database.py:68-80`) with FK enforcement, teardown and no global cross-request handle. Existing schema/data are not automatically reseeded on ordinary boot. Optional demo credentials come from environment and are deliberately legacy-form only for demo upgrade; this is documented, not an undisclosed deployed secret.

Explicit MVC is supported by code responsibility, not folder labels. Products: `routes/product_routes.py:9-17` maps verbs/guards → `controllers/product_controller.py:11-55` adapts fields/status/errors → `services/product_service.py:11-48` shares validation → `models/product_model.py:13-79` binds SQL and serializes product fields. Customer: `routes/user_routes.py:9-14` → `controllers/user_controller.py:11-55` → `models/user_model.py:22-72`; password hashing and controlled legacy upgrade precede token issuance. Orders: `routes/order_routes.py:9-15` → `controllers/order_controller.py:12-40` → `services/order_service.py:26-95` transaction/business decisions → `models/order_model.py:7-94`. Reports: `routes/report_routes.py:8` → controller → report policy service → aggregate model. Administration: guarded routes → admin controller → AdminModel; raw SQL remains intentionally functional behind admin authorization.

`auth.py:26-74` verifies a timed signed token then reloads current account/role; owner/admin guards and explicit POST order ownership prevent caller-supplied IDs granting access. Tokens contain an ID, not password. Health excludes secret/db_path/debug disclosure (`controllers/system_controller.py:21-28`). Configuration requires an external secret and timezone-aware legacy cutoff (`config.py:18-23`). Models contain no request/response objects; UserModel's current_app dependency reads configuration, a residual framework coupling rather than proof MVC is absent. No layer rewrite is warranted.

### Complete current contract inventory

| Methods/path | Route source | Current access and result boundary |
| --- | --- | --- |
| GET /; GET /health | routes/system_routes.py:7-8 | Public; 200 legacy message map / safe health/counts |
| GET /produtos; GET /produtos/busca; GET /produtos/<int:product_id> | routes/product_routes.py:9-11 | Public; list/search/detail envelopes, search q/categoria/preco_min/preco_max; missing404 |
| POST /produtos; PUT /produtos/<int:product_id>; DELETE /produtos/<int:product_id> | routes/product_routes.py:12-17 | Admin; create201/update200/delete200; invalid400/missing404; referenced delete409 |
| GET /usuarios; GET /usuarios/<int:user_id> | routes/user_routes.py:9-12 | Admin list / owner-or-admin detail; safe dados/sucesso; missing404 |
| POST /usuarios; POST /login | routes/user_routes.py:13-14 | Public registration201; login200 adds token/expires_in; invalid400, credentials401 |
| POST /pedidos; GET /pedidos | routes/order_routes.py:9-10 | Authenticated owner-or-admin creation201; admin all-order list200 |
| GET /pedidos/usuario/<int:usuario_id> | routes/order_routes.py:11-13 | Owner/admin list200 |
| PUT /pedidos/<int:pedido_id>/status | routes/order_routes.py:14-16 | Admin; controlled transition200, invalid400/missing404/conflict409 |
| GET /relatorios/vendas | routes/report_routes.py:8 | Admin; 200 dados/sucesso with totals/status/discount fields |
| POST /admin/reset-db; POST /admin/query | routes/admin_routes.py:8-9 | Admin; real reset and arbitrary SQL SELECT/write remain; SQL empty400/error500; successful envelopes preserved |

19 explicit pairs; variable names changed internally, URL syntax unchanged. Automatic HEAD/OPTIONS excluded.

### Phase 2 findings and catalog matrix

Initial static review found **one MEDIUM correctness regression R-C01**; it was communicated immediately and corrected concurrently by the parent. Final static reread sees that correction. No confirmed remaining CRITICAL/HIGH security finding was established by this review. This is not a claim of complete security or runtime correctness.

**R-C01 — MEDIUM — empty sales report status counts became null (discovered, then corrected).** Baseline `models/report_model.py:9-11` used SUM(CASE...) without COALESCE; on zero orders SQLite SUM returns NULL, and `services/report_service.py:25-27` forwarded it as pedidos_pendentes/aprovados/cancelados. Original COUNT paths returned numeric zero. Reproduction scenario: authenticated admin GET /relatorios/vendas before creating orders or after admin reset. Transformation proposed: wrap each status SUM with COALESCE(...,0), independent of architecture/auth dependencies; preserve numeric fields/200/envelope. Verification requested: empty-order report assertions plus populated status fixture. Parent reports a RED regression then GREEN focused test and names `reports/evidence/project-1-empty-report-red.log`; **I did not open that log or execute the test**. Current source reread confirms all three COALESCE clauses. No data migration/contract change needed; code rollback would reintroduce the regression. Hash difference explicitly records the concurrent source correction.

| Catalog | Observed current evidence / disposition |
| --- | --- |
| AP-01 SQL injection | Domain values bound in all models, including LIKE search. Dynamic IN contains generated placeholders, not input syntax. AdminModel.execute accepts SQL intentionally behind verified admin route; no forced read-only restriction recommended. |
| AP-02 secrets | Config requires env secret, health serialization excludes sensitive fields; demo environment examples are placeholders. Error handlers return generic DB/internal errors. Exception logs may include runtime exception text; no proven reachable password leak established. |
| AP-03 God unit | Startup/routes/controllers/SQL/domain transactions separated; no single original monolith remains. Existing small policy services do not justify inventing another service/repository layer. |
| AP-04 credentials | New passwords use Werkzeug scrypt; legacy plaintext comparison uses UTF-8 bytes + constant-time compare before explicit cutoff, valid login persists upgrade; modern hash failure never falls back to plaintext. Timed signed tokens. Legacy acceptance remains documented controlled migration exposure until cutoff, not eliminated plaintext history. |
| AP-05 authorization | All sensitive method/path registrations guarded; order-create cross-user check in controller. Admin SQL/reset remain functional by design. |
| AP-06 lifecycle | flask.g connection and teardown; standard SQLite transaction behavior. |
| AP-07 atomicity | Order create and status update begin IMMEDIATE before relevant reads/writes; rollback on exception. Status decision read is inside transaction, so two cancellation requests cannot both restore stock from a stale pretransaction state. Aggregated repeated product IDs/positive integer quantities and conditional stock update. |
| AP-08 N+1 | Order retrieval uses parent query plus one bulk item/product LEFT JOIN, not nested per-item lookups; totals aggregate once. Placeholder count can hit SQLite variable limits on very large all-order result sets: scale candidate, not measured defect in supplied evidence. |
| AP-09 duplication | Shared product validator/serializer; list/detail contracts explicit. |
| AP-10 deprecation | No Query.get/utcnow candidate; runtime/deprecation verification not performed. |
| AP-11 policy constants | Named discount tiers and allowed transitions retain explicit business values. |
| AP-12 unused/opaque | No source-local confirmed unused import identified in this pass; public Portuguese request keys retained. |

Specific implementation checks requested by context were inspected, not presumed: `services/order_service.py:66-74` now reads status after BEGIN IMMEDIATE; `services/product_service.py:30-37` checks finite price (including OverflowError); order total `:41-43` checks isfinite; `models/user_model.py:61-64` validates cutoff and UTF-8 compare; `errors.py:37-42` preserves HTTPException response status/headers. Residual type/extreme-size limits remain candidates: descricao binding types and SQLite INTEGER range are not fully validated; enormous input can fail generically. They are not evidence of SQL injection or a new architectural defect. Search floating NaN/Infinity range behavior is likewise uncharacterized.

## ecommerce-api-legacy

### Phase 1: responsibility and dependency trace

CommonJS Express application exports an asynchronous app factory (`src/app.js:11-29`), with real server startup awaiting initialization (`src/server.js:3-8`). Configuration validates external >=32-byte secret, port, token TTL and opt-in demo credentials. SQLite defaults to :memory:; DB_PATH permits persistence. Schema initialization is transactional, no demo seed on existing users table. Additive legacy migration CLI requires an exclusive backup copy and explicit reset of ambiguous legacy credential formats; no migration or reset was executed.

MVC flows are explicit. Checkout route `src/routes/index.js:4` → checkoutController adapts public usr/eml/pwd/c_id/card → checkoutService owns identity/payment simulation/whole transaction → checkoutModels/userModel SQL. Financial report route `:5` → auth+adminOnly → reportController queued read → financialReportModel LEFT JOIN aggregation. Delete route `:6` → verified identity → userController ID mapping → userLifecycleService transaction rereads actor/role/active and handles history-preserving deactivate vs hard delete → userModel. Added login route `:3` → authController → authService → userModel + scrypt/timed HMAC token primitives. Database, security, validation and error mapping are supporting concerns; no God Class remains.

### Complete current contract inventory: 4 pairs

| Method/path / source | Current input/access | Success, negative and effect boundaries |
| --- | --- | --- |
| POST /api/auth/login — src/routes/index.js:3 | Public {email,password} | 200 access_token/token_type/expires_in;400 input/401 invalid,inactive,reset-required |
| POST /api/checkout — :4 | Optional Bearer; public legacy keys usr/eml/pwd/c_id/card; existing user needs own token or password, new user >=8-char password | 200 msg/enrollment_id;400 input/payment denied,401 identity,404 inactive/missing course,500 DB; atomic account/enrollment/payment/audit |
| GET /api/admin/financial-report — :5 | Active administrator Bearer | 200 course/revenue/students array;401/403;500 generic DB |
| DELETE /api/users/:id — :6 | Active owner or administrator; safe positive integer ID | 200 JSON msg/id/action; histories cause deactivate rather than erase;400/401/403/404/500 |

### Phase 2 findings and catalog matrix

**No confirmed new CRITICAL/HIGH/MEDIUM/LOW finding** from this bounded static pass. No artificial minimum was imposed. The absence of findings means no additional refactoring proposal is justified, not that runtime tests or external security review are unnecessary.

| Catalog | Observed evidence / disposition |
| --- | --- |
| AP-01 | Request values parameterized in models; migration ALTER identifiers are fixed internal map keys. |
| AP-02 | No hardcoded usable gateway/SMTP credential; no card/password/token in checkout event (`services/checkoutService.js:26-27`); sample env placeholders explicit. |
| AP-03 | Application composition, routes, controllers, services, models and startup have distinct responsibilities. |
| AP-04 | security/passwords.js uses random salt + configured scrypt, validated stored format, constant-time compare. Token signature/audience/ID/time/expiry checked. Legacy ambiguous credentials blocked until reset. |
| AP-05 | Admin report middleware; checkout matches own account by token/password; lifecycle transaction rereads current actor/role/active; no public admin promotion. |
| AP-06 | One connection is deliberately queued; all read and transaction operations share queue, transaction retains it through awaits (`db/connection.js:18-35`). This is not the unsafe Python global-connection pattern. |
| AP-07 | checkout transaction includes new account, enrollment, payment, audit; denial precedes account insert; throw rolls back; logger failure cannot turn committed result into HTTP failure. Deletion/deactivation atomic and historical data retained. |
| AP-08 | One report query, LEFT joins preserve empty courses/missing users/payments; correlated earliest-payment selection avoids migrated multiple-payment fan-out. SQL correlated subquery is not a per-row network/driver query; query plan/cost still unmeasured. |
| AP-09 | Input mapping centralized; no material divergent duplicate validation confirmed. |
| AP-10 | No applicable deprecated API confirmed; runtime/official advisory lookup outside scope. |
| AP-11 | Named scrypt cost/card simulation/TTL bounds; teaching payment prefix intentionally preserved. |
| AP-12 | Opaque internal checkout names and unused globalCache/totalRevenue removed; public legacy field names preserved. |

Limits/candidates: no pagination/rate limiting is established as an approved requirement; scrypt work and request volume were not load-tested. No privilege-race exploit demonstrated by static middleware/queued read inspection; do not label this proven secure under arbitrary concurrent admin state changes. Existing legacy foreign-key/duplicate/orphan history is not rebuilt destructively: README documents preservation, startup rejects unmigrated schema, migration defaults all users to role user and reset-required. A usable admin provisioning workflow for a migrated production database requires trusted operator procedure; lack of a public promotion route is intentional. Auth middleware reloads identity on each request; password reset does not add per-token revocation versions. These are explicit operational/security-policy limits, not manufactured confirmed catalog findings.

## task-manager-api

### Phase 1: responsibility and dependency trace

Flask-SQLAlchemy scoped extension remains, with app factory no import-time create_all (`app.py:8-31`), explicit init-db and local debug-off startup. `seed.py` now refuses any nonempty table, uses supplied password and one commit/rollback, never deletes existing data. Models retain schemas and domain methods; shared date helper preserves naive UTC storage/output, replacing utcnow without inventing a timezone migration. Source uses db.session.get/select instead of Query.get.

MVC flows: task route `routes/task_routes.py:6-32` only adapts args/JSON/status → taskController authenticates/coordinates ownership/validation/serialization → repository.tasks/save/get/delete SQLAlchemy. User routes → userController public registration vs owner/admin mutation, legacy credential migration, safe serialization → repository + User domain password functions. Reports route → reportController owner/admin/report calculations → eager repository.users/tasks/categories; categories have own route/controller/entity path. Repository owns persistence, shared helpers own validators/serializers/constants. No new general service layer is required. Controllers' domain aggregation and existing reusable predicate are proportionate; no God Class inference from compressed style.

### Complete current contract inventory: 22 pairs

| Methods/path | Route source | Current access/result boundary |
| --- | --- | --- |
| GET /; GET /health | app.py:20,22 | Public200 message/version, health200 status/timestamp or503 unavailable |
| GET /tasks; GET /tasks/<int:task_id> | routes/task_routes.py:6,10 | Auth owner-visible/admin global; list includes names/overdue, detail overdue;404 missing |
| POST /tasks; PUT /tasks/<int:task_id>; DELETE /tasks/<int:task_id> | :14,18,22 | Auth owner/admin;201 task/200 task/200 message; invalid400,forbidden403,missing404 |
| GET /tasks/search; GET /tasks/stats | :26,30 | Owner-filtered/admin global;200 base task array / statistics |
| GET /users; GET /users/<int:user_id> | routes/user_routes.py:6,10 | Admin list / owner-admin detail; safe serializer, list task_count/detail tasks |
| POST /users; PUT /users/<int:user_id>; DELETE /users/<int:user_id> | :14,18,22 | Public ordinary registration201; owner/admin update200/delete200; role/active modifications admin only; delete also deletes tasks |
| GET /users/<int:user_id>/tasks; POST /login | :26,30 | Owner/admin tasks200; public credentials200 safe user + token;401 bad/403 inactive |
| GET /reports/summary; GET /reports/user/<int:user_id> | routes/report_routes.py:6,10 | Admin summary / owner-admin user report200 |
| GET /categories; POST /categories | routes/category_routes.py:6,10 | Auth list200; admin create201 |
| PUT /categories/<int:cat_id>; DELETE /categories/<int:cat_id> | :14,18 | Admin update200/delete200; category delete unlinks tasks per ORM relationship/policy, preserves task records |

### Phase 2 findings

Baseline review confirmed **two MEDIUM behavior differences and one LOW unused-import finding**; the MEDIUM entries were immediately sent to parent for decision/correction. Concurrent fixes were subsequently reread and confirmed statically. That reread also discovered a new MEDIUM error-string encoding regression R-T04, immediately sent to parent. No confirmed CRITICAL/HIGH security defect was established. Final dispositions are appended below rather than silently replacing discovery history.

**R-T01 — MEDIUM — search semantics differ.** `controllers/task_controller.py:23-25` lowercases input and performs Python substring search after loading all visible tasks. Original ORM used SQL LIKE('%q%'); therefore `%`/`_` query characters used as SQL wildcards are now literal, and SQLite LIKE case behavior differs from Unicode str.lower. Example q='%' used to match ordinary nonempty titles, now only titles containing percent. Local README does not document this search-semantics change. This is a contract-correctness issue, not SQL injection. Proposed narrow transformation: pass q through bound ORM LIKE predicates in repository while retaining owner/admin visibility/filter policies; no new service/layer. Test %, _, literal apostrophe, ASCII/Unicode case, absent/null descriptions, ordinary search and owner isolation. Independent of credential/security changes, no migration, rollback is code-only. Intended contract effect: restore original search semantics, preserve current authorized visibility. Parent correction status recorded below; this evaluator makes no edit.

**R-T02 — MEDIUM — omitted descriptions lose legacy empty-string defaults.** `utils/validation.py:19-22,61-64` only includes description if supplied; `controllers/task_controller.py:34-44`/`controllers/category_controller.py:11-14` instantiate and assign resulting values; `models/task.py:10`/`models/category.py:9` nullable columns have no default. POST /tasks and POST /categories with omitted description therefore store/return null instead of original data.get('description','') empty string. Difference is visible in creation and later reads. Explicit description:null should remain allowed where policy permits; omitted vs explicit null must stay distinct. Narrow fix: create-only default ''; preserve partial PUT semantics. Test omitted/present empty/present null and PUT omission. Independent no migration necessary; existing unintended null rows need retention decision before mass conversion. No blanket rewrite/backfill authorized.

**R-T03 — LOW AP-12 — unused local imports.** `routes/report_routes.py:1` imports request although both handlers take only path args and call controllers; `utils/serialization.py:1` imports format_date but serialization uses overdue and model.to_dict. Whole-file reads prove these local symbols unused; shared modules themselves remain used. Proposed remove only these two local imports, no public helper/service deletion; eventual boot/import check sufficient. No contract/data effect or dependency. An initial suspicion that reportController.authenticate was unused was withdrawn: it is used in user_report line20. This correction prevents a false-positive deletion.

| Catalog | Current evidence / disposition |
| --- | --- |
| AP-01 | No raw untrusted SQL; ORM expressions/session.get and fixed health SELECT1. Old ORM f-string LIKE was also bound, not injection. R-T01 addresses semantics only. |
| AP-02 | Safe User.to_dict excludes password; environment config for secret/SMTP; no route sends SMTP. No usable hardcoded credential found. |
| AP-03 | Routes adapt HTTP, controllers coordinate, entities/repos handle persistence; useful original mappings kept. No new layer proposed. |
| AP-04 | Scrypt for new passwords; MD5 recognized only 32-hex legacy before cutoff; active check before persisted upgrade; timed signed token verified. Existing legacy hashes remain until upgrade/reset, as documented. |
| AP-05 | Owner/admin checks on individual tasks/users and task assignment; admin-only lists/summary/category writes; registration forbids role/active escalation; account current state loaded per request. |
| AP-06 | Scoped Flask-SQLAlchemy session retained, no unsafe global sqlite handle. |
| AP-07 | User+task deletion one commit via repo.delete, global API/storage/unexpected error handlers rollback. Save validation precedes field mutation; no confirmed multi-commit business operation defect. Seed now non-destructive/refuses nonempty. |
| AP-08 | tasks eager joinedload user/category, users/categories selectinload tasks; no confirmed remaining N+1. Collections still load full tables: unbounded scale limit documented, not invented pagination scope. |
| AP-09 | task serializer contexts preserve list/detail/user-task field differences; validation shared. R-T02 shows a specific omitted-value bug, not cause to duplicate validators. |
| AP-10 | Query.get/utcnow absent from application paths; official runtime deprecation verification not independently performed. |
| AP-11 | Shared title/status/role/priority constants. Remaining password minimum4 is a documented retained business rule, not independently approved to raise. |
| AP-12 | R-T03 two local unused imports only; retained public helpers/NotificationService absence of callers does not prove globally safe deletion. |

Additional candidates not counted: source default secret only requires nonempty, not entropy validation (operator must supply strong random value); invalid cutoff/token TTL configuration could fail at request/startup, not shown as exploitable remote defect. Flask HTTPException adapter returns error/status without copying original headers; unknown method Allow header behavior deserves characterization, distinct from restored 405 status. Existence-vs-ownership 404/403 ordering and token revocation after password change need explicit policy, not opportunistic changes. None is silently declared fixed or escalated without verification.

## Approval surface, transformations and second-run stability

No further Phase 3 is performed by this evaluator. The only proposed follow-ups are R-C01 empty numeric counts (parent already corrected), R-T01 search semantics, R-T02 omitted descriptions and optional R-T03 import cleanup. All are narrow changes with code rollback; none requires adding layers/dependencies or changing auth/retention. If a new isolated skill execution were continued, explicit approval would be requested for the presented IDs and contract effects before edits; this delegated evaluation authorizes only the external report. No new install, server, DB or source write is authorized by this report. No findings are manufactured to meet a target.

Observed intentional differences relative to originals remain approval/validation items, not unresolved security defects simply because they change behavior: protected routes now return401/403; safe serializers remove secrets/hashes; real login credentials/tokens added (Node adds POST /api/auth/login); migrations/cutoffs/reset policy replace weak credentials; malformed inputs return400; Node lifecycle returns JSON and soft-deactivates historical users; direct-SQL product historical deletion rejects409; order status transitions/cancellation stock restore are explicit business changes; seeds/initialization/production debug behavior changed. This audit cannot reconstruct original human approval from current source; local README records the resulting policy. It does not assume documentation alone proves all changes were approved.

| Acceptance dimension | Direct static observation | Runtime evidence status in this audit |
| --- | --- | --- |
| All routes inventoried | 19 / 4 /22 explicit pairs | Not exercised |
| MVC boundaries | Traceable routes→controllers→models, meaningful services | Boot/import cycles not executed |
| Authorized success preserved | Admin SQL remains arbitrary and writable; protected handlers retain real operations | No HTTP authorization matrix run here |
| Secret/password exposure | Safe serializers and configured secrets observed | No captured response/log sentinel tests run here |
| Atomic writes | SQLite locks/rollback, Node queue, scoped ORM commit/rollback visible | No induced failure/concurrency test run here |
| Migration preservation | Explicit backup/cutoff/reset/non-destructive seed policies visible | No real DB opened/migrated |
| Query count | Bulk/eager query structures visible | No SELECT count or load benchmark run here |
| Contract stability | R-C01/R-T01/R-T02 identified; corrections tracked explicitly | Parent-reported results are not independent evaluator runs |
| Source immutability | Evaluator made no source writes | Concurrent parent fixes make global before/after equality false; exact diff below |

This second pass supports the skill's ability to retain already adequate architecture and identify smaller contract regressions without reintroducing a God-Class finding or forcing a minimum count. It does **not** prove a clean final HTTP acceptance matrix, identical repeated outputs across models, or absence of all vulnerabilities.
+

## Concurrent correction record and final dispositions

The implementer corrected R-T01 in current `models/repository.py:11-17`: q becomes a bound SQL LIKE predicate, owner constraint remains in the same query; `controllers/task_controller.py:10-23` passes search to repository instead of Python substring matching. R-T02 is corrected in `utils/validation.py:22,65` by create-only description defaults, followed by supplied-value handling, preserving PUT omission. R-T03 imports are removed in `routes/report_routes.py:1` and `utils/serialization.py:1`. These observations are from my own production-source reread. Parent reports 68/68 Task tests and 22/22 real HTTP success and P1 43/43 full tests; **I did not run or open these test results** and do not use them as independently verified evidence.

During that reread, **R-T04 — MEDIUM — public error strings acquired mojibake** was confirmed by `rg` in three concurrently rewritten Task files: `utils/validation.py:7,12,16,25,28,37,41,52,55,58,68`, `controllers/task_controller.py:16`, `models/repository.py:8`. For example, the previously proper Portuguese invalid-data literal became `Dados invÃ¡lidos`, and not-found became `Recurso nÃ£o encontrado`. This is actual matching source text, not merely a terminal-rendering hypothesis. It changes JSON error messages. Narrow transformation: repair encoding to UTF-8 text once, preserve exact messages/status, test malformed body/filter and missing record Unicode response. No migration/dependency/layer change; reported immediately to parent. Final repair status and manifest follow.

R-T04 final status: **corrected by implementer during audit**. Final production reread/rg finds no mojibake in the three affected files, and directly sees proper Portuguese literals plus the earlier LIKE/default fixes. Parent reports a focused exact-JSON Unicode test RED→GREEN (1 passed,65 deselected); this remains parent-reported, not independently executed by me. All discovered findings are now statically corrected: R-C01 MEDIUM; R-T01 MEDIUM; R-T02 MEDIUM; R-T03 LOW; R-T04 MEDIUM. **Remaining confirmed findings at final reread: CRITICAL0/HIGH0/MEDIUM0/LOW0** within this scope; candidates/limits above remain unverified rather than declared absent. No additional architecture rearrangement is proposed.

## Complete source/support/skill identity manifest

Baseline vs final: **116 paths before and after, 0 added,0 removed,6 changed**. Changed code belongs to concurrent implementer corrections: code-smells-project/models/report_model.py and task-manager-api/{controllers/task_controller.py,models/repository.py,routes/report_routes.py,utils/serialization.py,utils/validation.py}. All24 Node source files and all21 embedded skill files retain identical hashes. Other110 included files unchanged. This is **not** an unchanged-worktree claim: active implementation occurred while the evaluator remained read-only. Excluded runtime/test/cache/report paths were not hashed. Final observed Git HEAD may later change on commit; hashes below identify inspected content independently of HEAD.

| Project-relative path | Bytes baseline/final | SHA256 baseline | SHA256 final |
| --- | --- | --- | --- |
| code-smells-project/.agents/skills/refactor-arch/references/anti-patterns.md | 2615/2615 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 |
| code-smells-project/.agents/skills/refactor-arch/references/audit-report-template.md | 1278/1278 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 |
| code-smells-project/.agents/skills/refactor-arch/references/mvc-guidelines.md | 1560/1560 | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D |
| code-smells-project/.agents/skills/refactor-arch/references/project-analysis.md | 2143/2143 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 |
| code-smells-project/.agents/skills/refactor-arch/references/refactoring-playbook.md | 13092/13092 | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF |
| code-smells-project/.agents/skills/refactor-arch/references/validation.md | 1376/1376 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 |
| code-smells-project/.agents/skills/refactor-arch/SKILL.md | 5257/5257 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 |
| code-smells-project/.env.example | 544/544 | 1CC658EF0EF0F416CFA661B34D8C88825D9C9AE9C59CFE87A0F43662B28F92B8 | 1CC658EF0EF0F416CFA661B34D8C88825D9C9AE9C59CFE87A0F43662B28F92B8 |
| code-smells-project/app.py | 816/816 | 4EF25647A3A49F9AC194952B042894198F99F56A25E6B1E4D4C48608000F22F2 | 4EF25647A3A49F9AC194952B042894198F99F56A25E6B1E4D4C48608000F22F2 |
| code-smells-project/auth.py | 1978/1978 | 5B7816215819320B8C77E4A892DC95DC574D30C9440488A1E84DFCA3FA64633C | 5B7816215819320B8C77E4A892DC95DC574D30C9440488A1E84DFCA3FA64633C |
| code-smells-project/config.py | 745/745 | 2CB2740BABA46D81BE05301179D29E6773AC4644A642806D7AA69C440018563C | 2CB2740BABA46D81BE05301179D29E6773AC4644A642806D7AA69C440018563C |
| code-smells-project/controllers/__init__.py | 43/43 | 9F2AAB183991FC79666DA1ABFC4DF5FB287F75C3D8AEE7EDAC48CBB8675A73AA | 9F2AAB183991FC79666DA1ABFC4DF5FB287F75C3D8AEE7EDAC48CBB8675A73AA |
| code-smells-project/controllers/admin_controller.py | 690/690 | 7D7D5CCE6EA38FECDB605F35A54CAE8076A26CBA338141DBAA1CA4F23E6B41E0 | 7D7D5CCE6EA38FECDB605F35A54CAE8076A26CBA338141DBAA1CA4F23E6B41E0 |
| code-smells-project/controllers/order_controller.py | 1357/1357 | D2EE6DC5AF685C418E6D71521A3ED4D637BC05EF22D8F6B7B311B60C8382C5E3 | D2EE6DC5AF685C418E6D71521A3ED4D637BC05EF22D8F6B7B311B60C8382C5E3 |
| code-smells-project/controllers/product_controller.py | 1928/1928 | 25114FFA275D88DF4CDF44C8B75BE5C89C6C43A7F33573299E8FDD80EBB92A8E | 25114FFA275D88DF4CDF44C8B75BE5C89C6C43A7F33573299E8FDD80EBB92A8E |
| code-smells-project/controllers/report_controller.py | 184/184 | 20E44C658F3D45E1DCBBF45D257CDAC0A0FED259C997EB6E66758E2AC49C96D2 | 20E44C658F3D45E1DCBBF45D257CDAC0A0FED259C997EB6E66758E2AC49C96D2 |
| code-smells-project/controllers/system_controller.py | 656/656 | C042F2857A61D8728C1F5CF8BB13E9A0B6E37DC77ED9DFA2345D9A2C2D9CC540 | C042F2857A61D8728C1F5CF8BB13E9A0B6E37DC77ED9DFA2345D9A2C2D9CC540 |
| code-smells-project/controllers/user_controller.py | 1942/1942 | 51872AA058ED9F28D6F4DC315BB738A337D58D22DB82AF7602DB3F964583371A | 51872AA058ED9F28D6F4DC315BB738A337D58D22DB82AF7602DB3F964583371A |
| code-smells-project/database.py | 4520/4520 | A776F2CA01E5699819F0787AB061BB5691D3CDF8DCD3637CB21A91BFEC69A1A8 | A776F2CA01E5699819F0787AB061BB5691D3CDF8DCD3637CB21A91BFEC69A1A8 |
| code-smells-project/errors.py | 1607/1607 | A15032EA655ED1DD8554C1305D50A2B42D0725DD64C1DC5F8CFC6566DB05DFF2 | A15032EA655ED1DD8554C1305D50A2B42D0725DD64C1DC5F8CFC6566DB05DFF2 |
| code-smells-project/models/__init__.py | 49/49 | 732FD79CABA42836D45B08F294211086AD29C4943A5515503A11C51260CD2EB6 | 732FD79CABA42836D45B08F294211086AD29C4943A5515503A11C51260CD2EB6 |
| code-smells-project/models/admin_model.py | 770/770 | 4A5040D013A311FF98536C36415103E1826FAF9B5E4A206009E3C2526B185BCB | 4A5040D013A311FF98536C36415103E1826FAF9B5E4A206009E3C2526B185BCB |
| code-smells-project/models/order_model.py | 3225/3225 | 88BF78A09E2FAF2EBD382417DCDA633781DEFBB248B76D31BE9ABBCE2F5D7881 | 88BF78A09E2FAF2EBD382417DCDA633781DEFBB248B76D31BE9ABBCE2F5D7881 |
| code-smells-project/models/product_model.py | 2609/2609 | 122E740A19CBC6951285F064AFA58C5FB5DB1D582E964373F5EF3181078050ED | 122E740A19CBC6951285F064AFA58C5FB5DB1D582E964373F5EF3181078050ED |
| code-smells-project/models/report_model.py | 551/590 | F28B06DF556A4ACAC78BEED4381959D9DDBEFE06074981820BD188BFC4682993 | 51BDB82BD595EBAA2515436A1C5782549A397AF25FCD887258C79C93A32540DC |
| code-smells-project/models/system_model.py | 349/349 | F8128FDA60A0F9424C6D9D2AD2975E21FF95C36E6CD275629F99EE8D3167279B | F8128FDA60A0F9424C6D9D2AD2975E21FF95C36E6CD275629F99EE8D3167279B |
| code-smells-project/models/user_model.py | 2464/2464 | 5FBD900C325659C06FE228077CC6252284BEBF2365A2C456DDBC9D1D02F7AA75 | 5FBD900C325659C06FE228077CC6252284BEBF2365A2C456DDBC9D1D02F7AA75 |
| code-smells-project/README.md | 2130/2130 | D7FD48CC8BFC098FAC4EEA900831650D5D2F83968FF2205982F1BFFCA3244874 | D7FD48CC8BFC098FAC4EEA900831650D5D2F83968FF2205982F1BFFCA3244874 |
| code-smells-project/requirements-dev.txt | 34/34 | 3C3AD6730CF0C0417B77BAE38E53C11FA8CD96A34F2F8956998BAFC0AAF3EF17 | 3C3AD6730CF0C0417B77BAE38E53C11FA8CD96A34F2F8956998BAFC0AAF3EF17 |
| code-smells-project/requirements.txt | 33/33 | 9920665BD7C8D475DEE2EEE94465F9F02B2ECD834B1975A058A0206CD91CDDE4 | 9920665BD7C8D475DEE2EEE94465F9F02B2ECD834B1975A058A0206CD91CDDE4 |
| code-smells-project/routes/__init__.py | 489/489 | 44D477BED54139FEB199FE8FCA7056F7F790EB4F607D552182E8CB805FE73ED9 | 44D477BED54139FEB199FE8FCA7056F7F790EB4F607D552182E8CB805FE73ED9 |
| code-smells-project/routes/admin_routes.py | 308/308 | 2882AAB10577ABB6234B01E6C82A2BB4E79B3CEB402DB9BC03A7510C55086AE2 | 2882AAB10577ABB6234B01E6C82A2BB4E79B3CEB402DB9BC03A7510C55086AE2 |
| code-smells-project/routes/order_routes.py | 553/553 | 595AA27C5F505BDDCE5CA1DA07545070ACC4E99ED69FA9C0C7AA14786A6E2DCA | 595AA27C5F505BDDCE5CA1DA07545070ACC4E99ED69FA9C0C7AA14786A6E2DCA |
| code-smells-project/routes/product_routes.py | 642/642 | 604A7344E12A019FEBEEFA134ED8C5E015512FB887BD69E714DFB0E728F58437 | 604A7344E12A019FEBEEFA134ED8C5E015512FB887BD69E714DFB0E728F58437 |
| code-smells-project/routes/report_routes.py | 233/233 | CDEB603E40E5FA207C730C3981BB33808D8CF0C452CC69224D80E2D44710C0D9 | CDEB603E40E5FA207C730C3981BB33808D8CF0C452CC69224D80E2D44710C0D9 |
| code-smells-project/routes/system_routes.py | 210/210 | 22411F1C7C1B55A30A0C38D7459D3C604DC10B3A685BCA398DB29E583E5E3DA1 | 22411F1C7C1B55A30A0C38D7459D3C604DC10B3A685BCA398DB29E583E5E3DA1 |
| code-smells-project/routes/user_routes.py | 438/438 | 17BB3434D4F0CEB8510D71E72AEFAC5B5D19A102449E74AEE3BDC463C4BE6797 | 17BB3434D4F0CEB8510D71E72AEFAC5B5D19A102449E74AEE3BDC463C4BE6797 |
| code-smells-project/services/__init__.py | 53/53 | 8A7098AF1C47AAF51C3834BDD222E9F7D19142530D4C9ECC714C9DC9E786E23D | 8A7098AF1C47AAF51C3834BDD222E9F7D19142530D4C9ECC714C9DC9E786E23D |
| code-smells-project/services/order_service.py | 3892/3892 | 119105B3713FA4FEED7AE540D9280909321B3B251190003F06C068366D7B09AD | 119105B3713FA4FEED7AE540D9280909321B3B251190003F06C068366D7B09AD |
| code-smells-project/services/product_service.py | 1564/1564 | F6270139B70541F1A521A3E4DEB711C7A6C43CDC1553B3FC494335CF17159AB4 | F6270139B70541F1A521A3E4DEB711C7A6C43CDC1553B3FC494335CF17159AB4 |
| code-smells-project/services/report_service.py | 957/957 | 055EA30CFECD48897824A67DDB9DBCFE1826DE7ADC48AAA158770645AF88EFF7 | 055EA30CFECD48897824A67DDB9DBCFE1826DE7ADC48AAA158770645AF88EFF7 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/anti-patterns.md | 2615/2615 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/audit-report-template.md | 1278/1278 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/mvc-guidelines.md | 1560/1560 | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/project-analysis.md | 2143/2143 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/refactoring-playbook.md | 13092/13092 | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF |
| ecommerce-api-legacy/.agents/skills/refactor-arch/references/validation.md | 1376/1376 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 |
| ecommerce-api-legacy/.agents/skills/refactor-arch/SKILL.md | 5257/5257 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 |
| ecommerce-api-legacy/.env.example | 292/292 | C3021BCD2E0B6E3111AA2A8879630735BD97EB8CA70BE305C3D6F62026F80900 | C3021BCD2E0B6E3111AA2A8879630735BD97EB8CA70BE305C3D6F62026F80900 |
| ecommerce-api-legacy/api.http | 1067/1067 | 43930D3039F47BA3F5589848D21E36EB09A067A81EB7656AF685CA68410D7925 | 43930D3039F47BA3F5589848D21E36EB09A067A81EB7656AF685CA68410D7925 |
| ecommerce-api-legacy/package-lock.json | 55382/55382 | 3E3E69870277794BC0599238A3572AB1A4C987A1F0C5C4BC73231D2695AE01A3 | 3E3E69870277794BC0599238A3572AB1A4C987A1F0C5C4BC73231D2695AE01A3 |
| ecommerce-api-legacy/package.json | 559/559 | 243F265B9B0F2B8446A3FD67CC27D736C029209DB8AE59284106FD240E8E1081 | 243F265B9B0F2B8446A3FD67CC27D736C029209DB8AE59284106FD240E8E1081 |
| ecommerce-api-legacy/README.md | 7356/7356 | 69B2009DB36CFE87CF488D1D5BAD1DB4B268D794DF724BF26311E9AD1631DE33 | 69B2009DB36CFE87CF488D1D5BAD1DB4B268D794DF724BF26311E9AD1631DE33 |
| ecommerce-api-legacy/src/app.js | 1523/1523 | 37DE1027CBD1A7F0B28BD1EAD23B7082C7453E7C0DC7B64B162FEF749CBE3180 | 37DE1027CBD1A7F0B28BD1EAD23B7082C7453E7C0DC7B64B162FEF749CBE3180 |
| ecommerce-api-legacy/src/config/index.js | 1189/1189 | 9DAC7B8226AB5B3241672A54E4923476C207649B5B0909138C541EE905A04F9D | 9DAC7B8226AB5B3241672A54E4923476C207649B5B0909138C541EE905A04F9D |
| ecommerce-api-legacy/src/controllers/authController.js | 201/201 | 2B185DDD253BEF64A8A8DF2439F3EBAD37A3092C1C1C4E1E490F139A13330C62 | 2B185DDD253BEF64A8A8DF2439F3EBAD37A3092C1C1C4E1E490F139A13330C62 |
| ecommerce-api-legacy/src/controllers/checkoutController.js | 177/177 | 86CF871C9FA92FC3D88A992A3D2D762D088469BFC1B791F69257E3703FF40E68 | 86CF871C9FA92FC3D88A992A3D2D762D088469BFC1B791F69257E3703FF40E68 |
| ecommerce-api-legacy/src/controllers/reportController.js | 367/367 | 745EC1CBA95988BBBA323734E16B75C551E5FF01601D33B1A0B5ABC35DF4DBF3 | 745EC1CBA95988BBBA323734E16B75C551E5FF01601D33B1A0B5ABC35DF4DBF3 |
| ecommerce-api-legacy/src/controllers/userController.js | 180/180 | 155FC917CF2290B0D944443C8DDE5641D749EC310A54C0CD484C18B9AD37CC9E | 155FC917CF2290B0D944443C8DDE5641D749EC310A54C0CD484C18B9AD37CC9E |
| ecommerce-api-legacy/src/db/connection.js | 1939/1939 | 5F6B36777A16B4989EC3A7ECB6B1B7900D3EEEDBAF07A678DB976F7BEB501140 | 5F6B36777A16B4989EC3A7ECB6B1B7900D3EEEDBAF07A678DB976F7BEB501140 |
| ecommerce-api-legacy/src/db/migrate-legacy.js | 2167/2167 | 91CD4A45E5D31A48C93D9BEB7ECE0C70DF789F6D336AE77E89F4AE9E255B4B32 | 91CD4A45E5D31A48C93D9BEB7ECE0C70DF789F6D336AE77E89F4AE9E255B4B32 |
| ecommerce-api-legacy/src/db/reset-password.js | 1328/1328 | 46B917A960611B0E9121F7A6E67F112E8112BC3B47BADA1A8C569F93519EA80E | 46B917A960611B0E9121F7A6E67F112E8112BC3B47BADA1A8C569F93519EA80E |
| ecommerce-api-legacy/src/db/schema.js | 2388/2388 | A1E1A41AB2BB4F160C305561D876A39FC1232FE2F102DA1DB4CC0025E85270B7 | A1E1A41AB2BB4F160C305561D876A39FC1232FE2F102DA1DB4CC0025E85270B7 |
| ecommerce-api-legacy/src/errors.js | 509/509 | 72C630FDAA344847D798ECA44AA2315504DE2C40EB132991B1ABADDA3571CFDD | 72C630FDAA344847D798ECA44AA2315504DE2C40EB132991B1ABADDA3571CFDD |
| ecommerce-api-legacy/src/middleware/authenticate.js | 735/735 | 30D54FD320BD9B12176E8E0D58BEB945054D7B44B4D09349CBB9FC400FF42FDB | 30D54FD320BD9B12176E8E0D58BEB945054D7B44B4D09349CBB9FC400FF42FDB |
| ecommerce-api-legacy/src/models/checkoutModels.js | 541/541 | 455524088E29B4192E437260A05CB06E560EA7C2BBE6AF87FF6649D9019C2518 | 455524088E29B4192E437260A05CB06E560EA7C2BBE6AF87FF6649D9019C2518 |
| ecommerce-api-legacy/src/models/financialReportModel.js | 1047/1047 | E6E6D9FF7E3AE7265FE3A9FDFDD00FA3151EDD91633B3DA6B45A17D899B7B256 | E6E6D9FF7E3AE7265FE3A9FDFDD00FA3151EDD91633B3DA6B45A17D899B7B256 |
| ecommerce-api-legacy/src/models/userModel.js | 627/627 | EBCE1AD88E3C7FB46610C98206468899C569547CE288962287D83DA41736FFC4 | EBCE1AD88E3C7FB46610C98206468899C569547CE288962287D83DA41736FFC4 |
| ecommerce-api-legacy/src/routes/index.js | 538/538 | CFAB4BD44223CA71DBB994532AB1239947A292E3C47F3D19041AEB8963FD9F0C | CFAB4BD44223CA71DBB994532AB1239947A292E3C47F3D19041AEB8963FD9F0C |
| ecommerce-api-legacy/src/security/passwords.js | 941/941 | F49AEE3172823C21EB7FE8B46E14D0E381BF1F3ECF8A997F90ED26DDC5AA4F38 | F49AEE3172823C21EB7FE8B46E14D0E381BF1F3ECF8A997F90ED26DDC5AA4F38 |
| ecommerce-api-legacy/src/security/tokens.js | 1510/1510 | 177532DA031DC9F9552F58E19F17DC0364474C49BA3881225A2E21F7B5018468 | 177532DA031DC9F9552F58E19F17DC0364474C49BA3881225A2E21F7B5018468 |
| ecommerce-api-legacy/src/server.js | 1450/1450 | 4E8AD7A110A63A163FED052FB3C5A307BE8C3B1CBE7DC377EB2D9EA9F9948F75 | 4E8AD7A110A63A163FED052FB3C5A307BE8C3B1CBE7DC377EB2D9EA9F9948F75 |
| ecommerce-api-legacy/src/services/authService.js | 1092/1092 | 961E5C6164FE6CEFEDDF70AFCF291AFB52AA5E04EB9B9FA25AB42E0F84F64B86 | 961E5C6164FE6CEFEDDF70AFCF291AFB52AA5E04EB9B9FA25AB42E0F84F64B86 |
| ecommerce-api-legacy/src/services/checkoutService.js | 1753/1753 | 11FBFA218A2A637ADDA7E6FCC19857BA73070DFE86E010714509D9521BC863C1 | 11FBFA218A2A637ADDA7E6FCC19857BA73070DFE86E010714509D9521BC863C1 |
| ecommerce-api-legacy/src/services/simulatedPaymentGateway.js | 195/195 | 2E7ED5735C9733E685545C43B56ED36A40AAB95CA0D170CF1C474D06306849A0 | 2E7ED5735C9733E685545C43B56ED36A40AAB95CA0D170CF1C474D06306849A0 |
| ecommerce-api-legacy/src/services/userLifecycleService.js | 1100/1100 | ED435D4889331E63A3EA5E61355BBF552A3A99EFB497D0FB0D746FA2B9433175 | ED435D4889331E63A3EA5E61355BBF552A3A99EFB497D0FB0D746FA2B9433175 |
| ecommerce-api-legacy/src/validation/inputs.js | 1265/1265 | 5B5B5AF777B5824BB0095CAD6FA9691115108451D8E4AB2849EEB11D9748A2F8 | 5B5B5AF777B5824BB0095CAD6FA9691115108451D8E4AB2849EEB11D9748A2F8 |
| task-manager-api/.agents/skills/refactor-arch/references/anti-patterns.md | 2615/2615 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 | 495F1F16FC7051C958CB5AA8360EF777E43E9D6EC25247B31427FA21B5C98924 |
| task-manager-api/.agents/skills/refactor-arch/references/audit-report-template.md | 1278/1278 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 | 3DB9EDC629385C83E7311088096009893A0AEA1F745D72CFFE968F2C9487A7D4 |
| task-manager-api/.agents/skills/refactor-arch/references/mvc-guidelines.md | 1560/1560 | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D | C3F87C2A18AFB3471B19411FEAAB919B2D1922C4EBAA5D2C9911876EA8F12C8D |
| task-manager-api/.agents/skills/refactor-arch/references/project-analysis.md | 2143/2143 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 | 8991985EBDED97D135E4B4E176DA7BD83646CD1DEBEC3C829E790066DEA29B49 |
| task-manager-api/.agents/skills/refactor-arch/references/refactoring-playbook.md | 13092/13092 | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF | 42052E8581ADBF30D5E11BC86B23BCF936927A6A08D7DD8D49429A692DB33FAF |
| task-manager-api/.agents/skills/refactor-arch/references/validation.md | 1376/1376 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 | 53CDEEFD5B0630582ACC891616AA09CE3284249EB0948759E608E588C2696238 |
| task-manager-api/.agents/skills/refactor-arch/SKILL.md | 5257/5257 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 | 0B17F6FC6AE3C12100455A45C9824BE0552B5DEC984F9FC33578A23952BFB115 |
| task-manager-api/app.py | 1317/1317 | F65255F165D255C820EB94881885C721687549D2977C8BE91B3C77B5A600A454 | F65255F165D255C820EB94881885C721687549D2977C8BE91B3C77B5A600A454 |
| task-manager-api/auth.py | 1195/1195 | C86D71EF41B97C4CDC316A4DCF31BC0A84BDB168F0D75DBC7F04B3442795B075 | C86D71EF41B97C4CDC316A4DCF31BC0A84BDB168F0D75DBC7F04B3442795B075 |
| task-manager-api/config.py | 379/379 | 4C000D7FEE6A6715B6D191AB37711375A9AE4DA53A8D89BF561834E4C9575804 | 4C000D7FEE6A6715B6D191AB37711375A9AE4DA53A8D89BF561834E4C9575804 |
| task-manager-api/controllers/__init__.py | 0/0 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 | E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 |
| task-manager-api/controllers/category_controller.py | 669/669 | CA628EDD25CF2807F1A92465761E0C6F680B6951CCD491BDD148242577CFFB3D | CA628EDD25CF2807F1A92465761E0C6F680B6951CCD491BDD148242577CFFB3D |
| task-manager-api/controllers/report_controller.py | 1767/1767 | 615C0D27FF89CB34C4FA53956ABC6D8323103AC3982FA10547211BB9634F3EE3 | 615C0D27FF89CB34C4FA53956ABC6D8323103AC3982FA10547211BB9634F3EE3 |
| task-manager-api/controllers/task_controller.py | 2407/2327 | A5F5C6026C2AAE289E1541D3574709E2F1BE749F7EE52B4BB0BAFF2127228F9A | 9DB53195479DAFF8DBE00429AA26F2958B015BC71C2D28D846BA7F33FED14965 |
| task-manager-api/controllers/user_controller.py | 2765/2765 | FB44E7E06647126BDF4C7F70F76992711C2101C807B8D6B077AD8F9E6AA792C0 | FB44E7E06647126BDF4C7F70F76992711C2101C807B8D6B077AD8F9E6AA792C0 |
| task-manager-api/database.py | 62/62 | 5F9AB7B94BDECC149AE3BB18BA50D60B07462C4C41A3A18809ADFD43F089A89C | 5F9AB7B94BDECC149AE3BB18BA50D60B07462C4C41A3A18809ADFD43F089A89C |
| task-manager-api/errors.py | 855/855 | D3B847EBB79423601BB504321DF8605A0E7C7BCA19EDFEE58968A5018BBE46C3 | D3B847EBB79423601BB504321DF8605A0E7C7BCA19EDFEE58968A5018BBE46C3 |
| task-manager-api/models/__init__.py | 98/98 | 89D61649A4486EC71BBF6292B34A39BF204490005A0672D9BD6329ECBA2CB1ED | 89D61649A4486EC71BBF6292B34A39BF204490005A0672D9BD6329ECBA2CB1ED |
| task-manager-api/models/category.py | 664/664 | C16EA39DA8524B70C05149C2D9A5C4E6E272638CBABE5C1BB9DF920C50F8D7EF | C16EA39DA8524B70C05149C2D9A5C4E6E272638CBABE5C1BB9DF920C50F8D7EF |
| task-manager-api/models/repository.py | 1076/1228 | BB3EC241772AD6776BD44201556FC8144D02B119067C8E8FE13B2643B98F3024 | DA30CC54D37252EFFBA7B0DD712A3D1464BFD101CD4B1CFD49CF61BE76E0F28C |
| task-manager-api/models/task.py | 1848/1848 | B804BC4247B5D87D2CF16316E03540CEB07201481D8B3D722507462CAB9CF75F | B804BC4247B5D87D2CF16316E03540CEB07201481D8B3D722507462CAB9CF75F |
| task-manager-api/models/user.py | 1178/1178 | D5D3CCF73DD5138A8806452C7192D52F1E8AC78BE59170AC6B7D4814A72A88C7 | D5D3CCF73DD5138A8806452C7192D52F1E8AC78BE59170AC6B7D4814A72A88C7 |
| task-manager-api/README.md | 4710/4710 | DFA7123C549A376B212664E74BD8434CAB0AB6A98A2FAF1357E33D0EEC368806 | DFA7123C549A376B212664E74BD8434CAB0AB6A98A2FAF1357E33D0EEC368806 |
| task-manager-api/requirements-dev.txt | 36/36 | AC3B9DAAD7613D985567E0C2EED70660E78729ECD1D49484B2952A6E92C6E505 | AC3B9DAAD7613D985567E0C2EED70660E78729ECD1D49484B2952A6E92C6E505 |
| task-manager-api/requirements.txt | 119/119 | C56CBF059924E9A56AE63017CAC7861DED0CFBDEE88792D59D0B8F99BD789F00 | C56CBF059924E9A56AE63017CAC7861DED0CFBDEE88792D59D0B8F99BD789F00 |
| task-manager-api/routes/__init__.py | 2/2 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 |
| task-manager-api/routes/category_routes.py | 762/762 | DDEEABFF672AA02602E9CA48A63C1545A44434F07F53B7543730EB34FDDBA0E3 | DDEEABFF672AA02602E9CA48A63C1545A44434F07F53B7543730EB34FDDBA0E3 |
| task-manager-api/routes/report_routes.py | 429/420 | 688E1294C57AB135D644A2EA4B42FA4F976F7BC950686CC995B9BA1970C4EE91 | AA1F68879D12FDE7051D5C1D2525EA2045891823799E764CC088F2D5D7BDB401 |
| task-manager-api/routes/task_routes.py | 1103/1103 | C6DC3A402D2E8B54E9E094CEA6E207434CF959AD437BE75D8B14F3705690A3FF | C6DC3A402D2E8B54E9E094CEA6E207434CF959AD437BE75D8B14F3705690A3FF |
| task-manager-api/routes/user_routes.py | 1120/1120 | 59D9B8626098B1FBA0283291CB39F485254C5501107AB1A22F63173F5338EFED | 59D9B8626098B1FBA0283291CB39F485254C5501107AB1A22F63173F5338EFED |
| task-manager-api/seed.py | 1198/1198 | 184411B613EC1129824D7B181F15F1808932BB5B4BBF320F6ACE64611C6BD270 | 184411B613EC1129824D7B181F15F1808932BB5B4BBF320F6ACE64611C6BD270 |
| task-manager-api/services/__init__.py | 2/2 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 |
| task-manager-api/services/notification_service.py | 1698/1698 | A1560183A54ADAE3F949CB2234EFCF3F35D210DAF9DEFC9A1AAB3078FD35117A | A1560183A54ADAE3F949CB2234EFCF3F35D210DAF9DEFC9A1AAB3078FD35117A |
| task-manager-api/utils/__init__.py | 2/2 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 | 7EB70257593DA06F682A3DDDA54A9D260D4FC514F645237F5CA74B08F8DA61A6 |
| task-manager-api/utils/constants.py | 262/262 | 3CBC34E2D54AF6F23F1D8A23DC675F8211AE1B4E0676537C7F1E076EDA8B926F | 3CBC34E2D54AF6F23F1D8A23DC675F8211AE1B4E0676537C7F1E076EDA8B926F |
| task-manager-api/utils/dates.py | 457/457 | 4A6AE876CF3092DD3900B6A6FD1B221F91F0FFFD740FEC8FB22A49E68EACE0A9 | 4A6AE876CF3092DD3900B6A6FD1B221F91F0FFFD740FEC8FB22A49E68EACE0A9 |
| task-manager-api/utils/helpers.py | 1235/1235 | DABDBFEA4DFE246112FAE45B5CCC37405AE1FD9FEFD7DCA76A6DE4EAFA6F254F | DABDBFEA4DFE246112FAE45B5CCC37405AE1FD9FEFD7DCA76A6DE4EAFA6F254F |
| task-manager-api/utils/serialization.py | 556/543 | DD7320F4D0D530B58DFDDD72BF0012C890610CA1403FF20F6535E9967727341E | 2BCFFEF3FBFEEC13EF1756FFE718AF34566B9CAE65A650ED9204BAA750FAD414 |
| task-manager-api/utils/validation.py | 3322/3404 | C437C79D37741C48AC95006BCF1DA70F3E1FE23E5B571361721080775E45247F | B39E8F595B4CEB0026AAD542670D0468414FFC1D3E983C7F68EE9E25C57FDEEC |

+
