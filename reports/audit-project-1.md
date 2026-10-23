# Phase 1–2 audit

## Approval record

- Original project revision: `6d1ce6248c3e956801010a89d8bdaab48029bf30`.
- Isolated audit revision: `f5ebe7fd3a31a8b03d64a3fa71175c2d4b20262d`.
- Skill package SHA256:
  `1848a52ef70992701552e275e4b3d998d83e94810a3c2e6cae05317e41d3bb57`.
- Human approval: on 2026-10-22, after reviewing the full audit and contract
  differences, the user requested severity and historical-text corrections and
  authorized continuation once adjusted: “uma vez ajustados, pode continuar”.
- Approved scope: all 15 confirmed findings and all contract differences below,
  including authentication/authorization, password migration, order transitions,
  referenced-product deletion policy, and retaining arbitrary SQL for verified
  administrators.
- Review correction: AUD-003, AUD-004 and AUD-005 are CRITICAL under the challenge
  rubric. The correction changes severity totals only; evidence, transformations,
  dependencies and contract differences are unchanged.

This approved audit was persisted before the first application-source edit.

Original execution evidence: [complete Phase 1/2 output](evidence/audit-project-1-phase-1-2-gpt-5.6.md)
and [event log](evidence/audit-project-1-phase-1-2-gpt-5.6-events.jsonl).

No files were written or modified. No dependencies were installed, no application imports or servers were started, and no database, seed, or Phase 3 action was executed.

## 1. Revision and analysis scope

| Item | Result |
|---|---|
| Project root | `C:\Users\eduar\AppData\Local\Temp\refactor-arch-project1-56-f34583fae7144a9ca48c29bc7915efdd\code-smells-project` |
| Branch / revision | `main` / `f5ebe7fd3a31a8b03d64a3fa71175c2d4b20262d` |
| Commit date | 2026-10-22 17:10:17 -03:00 |
| Working tree | Clean; no staged, modified, or untracked paths |
| Git caveat | Git could not read the user-level global ignore file because of permissions; repository status itself was still clean |
| Analysis date | 2026-10-22 |
| Repository instructions | No `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md` found |
| Skill | `refactor-arch`; no declared version; audited skill Git-blob hash `98b6b644bdb2077db66b48d4a311c199fbdb7469` |
| Explicit HTTP contracts | 19, excluding automatic `HEAD`/`OPTIONS` |
| Future report | `reports/audit-project-1.md` — directory and report do not currently exist |

### Analyzed sources

Exactly four Python source files were analyzed:

1. `app.py`
2. `controllers.py`
3. `models.py`
4. `database.py`

Also inspected as project metadata: `README.md` and `requirements.txt`.

Excluded from the source-file count:

- Seven `.agents/skills/refactor-arch` instruction/reference files, treated as audit tooling rather than application source.
- `.git` metadata.
- Nonexistent dependency, virtual-environment, cache, build, generated-output, report, and local-database files.
- `loja.db` was absent.
- No tests, lockfile, migration files, templates, or static assets exist in the repository.

## 2. Project analysis

### Stack and version confidence

| Component | Declared | Verified locally |
|---|---|---|
| Language | Python; no project version constraint | Python executable `3.12.10`; this is the audit environment, not a declared project requirement |
| Framework | Flask `3.1.1` | Unverified: Flask is not installed in the audit environment |
| CORS extension | Flask-CORS `5.0.1` | Unverified: package is not installed |
| Persistence driver | Python standard-library `sqlite3` | SQLite library `3.49.1` |
| Application API version | Response literals say `1.0.0` | Static source evidence only |

The pins in `requirements.txt` are declarations, not a reproducible installation: there is no lockfile or transitive dependency inventory. Runtime imports were deliberately not attempted because importing this application can initialize and seed a database.

### Domain and persistence

This is an e-commerce JSON API for:

- Products, inventory, categories, and search.
- Users and login.
- Orders, line items, status changes, and stock deductions.
- Sales reporting.
- Health reporting.
- Administrative database reset and arbitrary SQL execution.

Persistence is direct SQLite through a relative `loja.db` file. `database.get_db()` owns a process-global connection, creates four tables, and seeds products and users whenever it opens a database whose product table is empty (`database.py:4-84`). There are no foreign keys, uniqueness constraints, check constraints, schema versions, or migrations.

### Entry points

- Documented command: `python app.py` (`README.md:5-12`).
- Main block: initializes the database and starts Flask on `0.0.0.0:5000` with debug enabled (`app.py:80-88`).
- Importable WSGI object: module-global `app` (`app.py:6`), although no production WSGI command is documented.
- Route registration: `app.py:11-60`.
- Persistence/bootstrap entry: `database.get_db()`.

### Current responsibility map

| Unit | Current responsibilities and coupling |
|---|---|
| `app.py` | Creates/configures Flask, enables global CORS, registers every route, returns the index response, directly implements destructive admin routes, accesses SQLite, and starts the development server |
| `controllers.py` | Reads Flask requests, validates inputs, selects HTTP statuses, coordinates domain behavior, formats responses, emits simulated notification output, and directly executes health SQL |
| `models.py` | Owns raw SQL, serialization, authentication lookup, product/user/order/report logic, stock mutation, order totals, and discount rules |
| `database.py` | Owns connection lifecycle, schema creation, initial data, default credentials, and commits |
| Dependency direction | `app → controllers → models → database`; `app` and `controllers` also bypass boundaries and depend directly on `database` |

The project has controller/model filenames, but it is not clean MVC: routes and SQL exist in `app.py`, SQL exists in a controller, models span unrelated domains and business workflows, and startup/persistence/seeding are inseparable.

## 3. Severity summary

| Severity | Confirmed |
|---|---:|
| CRITICAL | 5 |
| HIGH | 4 |
| MEDIUM | 4 |
| LOW | 2 |
| Total | 15 |

One additional CORS concern is recorded as a suspicion and is not counted.

All catalog families were checked. AP-01 through AP-09, AP-11, and AP-12 have confirmed evidence. No application use of a deprecated API was found for AP-10; the declared Flask packages could not be checked dynamically because they are not installed.

## 4. Complete findings

### CRITICAL

#### AUD-001 — SQL injection in domain operations (AP-01)

- Evidence: `models.py:47-50`, `57-60`, `109-111`, `126-129`, `140-166`, `289-299`.
- Reachability: product creation/update/search, user creation/login, and order input originate in public HTTP request bodies or query parameters.
- Examples include login email/password concatenation and search text/category interpolation.
- Impact: authentication-query manipulation, cross-table disclosure through crafted search SQL, corrupted values, and unauthorized database changes.
- Transformation: bind every domain value through SQLite placeholders. Keep table/column identifiers fixed in code.
- Verification: quotes round-trip as data; login injection fails with 401; legitimate login/search/create/update/order behavior remains valid.
- Dependencies: parameterization is independent. The exceptional `/admin/query` trust boundary additionally depends on AUD-002.
- Contract effect: intentional difference—malicious SQL syntax becomes literal data or a normal validation/authentication failure.

#### AUD-002 — No authentication or authorization, including full administrative database control (AP-05)

- Evidence: all route registration in `app.py:11-30`; unauthenticated reset at `app.py:47-57`; unauthenticated arbitrary query at `app.py:59-78`.
- No token issuance, identity middleware, role check, ownership check, or verified upstream control exists anywhere in the repository.
- Reachable impact:
  - Any caller can read, modify, or drop database objects through `/admin/query`.
  - Any caller can erase all application data through `/admin/reset-db`.
  - User/password data, all orders, reports, product mutations, and status changes are public.
- Transformation: add verified, expiring authentication and centralized role/ownership authorization.
- Proposed policy:
  - Public: `/`, `/health`, product reads/search, registration, login.
  - Authenticated customer: create own orders and read own orders/account.
  - Administrator: user listing, product mutations, all-order/report access, status changes, reset, and SQL console.
- The authorized SQL console retains arbitrary SQL; it is not converted to a read-only endpoint or removed.
- Dependencies: AUD-003 for a protected signing key and AUD-005 for password hashing/token issuance.
- Contract effect: protected routes gain 401 and 403 outcomes; authorized success flows remain functional.

### CRITICAL — continued

#### AUD-003 — Hardcoded and publicly exposed secrets/default credentials (AP-02)

- Severity rationale: CRITICAL under the challenge rubric because fixed
  credentials are present and the signing secret is returned by a public endpoint.
- Evidence:
  - Flask signing key: `app.py:7`.
  - Same key returned publicly by health: `controllers.py:287-290`.
  - Default admin/customer passwords: `database.py:75-82`.
- Impact: secret disclosure, predictable credentials, inability to rotate configuration safely, and unsafe reuse if sessions/tokens are introduced.
- Transformation: require the signing key from external configuration, remove it from responses, rotate it, and remove production default credentials from implicit initialization.
- Dependencies: required by AUD-002 and AUD-005.
- Contract effect: health loses `secret_key`; startup fails clearly when required production configuration is missing; automatic default credential creation ends.

#### AUD-004 — Cross-domain God modules and misplaced responsibilities (AP-03)

- Severity rationale: CRITICAL under the challenge rubric because routing,
  persistence and complex rules are concentrated across God modules, constituting
  a complete separation-of-responsibilities violation.
- Evidence:
  - `controllers.py:5-292` mixes products, users, authentication, orders, reporting, notifications, persistence health checks, and HTTP mapping.
  - `models.py:4-314` mixes four domains, authentication, persistence, serialization, stock/order orchestration, and discount policy.
  - `app.py:47-78` places SQL and destructive use cases directly in the route/composition module.
  - `database.py:7-84` combines connection management, schema installation, and seed data.
- Impact: security and transaction rules cannot be enforced at one boundary; changes have broad regression scope; independent domain testing is difficult.
- Transformation: explicit routes, controllers, models/repositories, application composition, and a meaningful order service for transactional orchestration.
- Dependencies: foundational for centralized errors and useful for AUD-006, AUD-007, AUD-009, and AUD-012.
- Contract effect: preserved except for separately listed security and correctness differences.

#### AUD-005 — Plaintext password storage and password disclosure (AP-04)

- Severity rationale: CRITICAL because public endpoints disclose stored passwords.
  Insecure password storage without disclosure would be HIGH; the confirmed data
  exposure controls the severity of this combined finding.
- Evidence:
  - Plain `senha TEXT`: `database.py:27-34`.
  - Plaintext seeds: `database.py:75-82`.
  - Plaintext insert/comparison: `models.py:105-130`.
  - Password returned by list/detail serializers: `models.py:72-103`.
- Impact: every stored password is exposed by public user endpoints and by database compromise; password reuse elsewhere becomes vulnerable.
- Transformation: Werkzeug scrypt hashes with unique salts, constant-time verification, expiring signed access tokens, and no hash/password serialization.
- Dependencies: token signing requires AUD-003; authorization requires the result.
- Contract effect: user responses omit `senha`; successful login adds token metadata; stored password values change irreversibly to hashes.

### HIGH

#### AUD-006 — Process-global, cross-request SQLite connection (AP-06)

- Evidence: `database.py:4-11`, including `global db_connection` and `check_same_thread=False`.
- Impact: requests share transaction and cursor state; one failed request can leave changes that a later request commits; concurrent use is unsafe.
- Transformation: application-configured, request-scoped connection in Flask `g`, teardown closure, foreign keys enabled per connection, and explicit transaction ownership.
- Dependencies: should accompany application composition in AUD-004.
- Contract effect: HTTP behavior preserved; connection/transaction lifetime changes internally.

#### AUD-007 — Multi-step writes lack reliable rollback (AP-07)

- Evidence:
  - Order creation inserts an order, inserts multiple line items, updates stock, and only commits at the end (`models.py:133-169`), but has no rollback block.
  - Database reset performs four deletes before a final commit (`app.py:47-55`) with no rollback handling.
  - AUD-006 allows a later request to commit a transaction left open by a failure.
- Impact: partial orders, partial inventory changes, or partially reset data can survive after exceptions.
- Transformation: explicit transactional order/reset use cases with rollback on all failures.
- Dependencies: AUD-006 and the order-service boundary from AUD-004.
- Contract effect: successful responses stay the same; failures guarantee no partial durable effect.

#### AUD-008 — Development debugger exposed on all interfaces (SEC-01, outside catalog)

- Evidence: `DEBUG=True` at `app.py:8`; development server on `0.0.0.0` with `debug=True` at `app.py:88`; health claims `ambiente: producao` at `controllers.py:285-289`.
- Impact: development diagnostics and debugger behavior may be exposed on a network when the documented startup command is used.
- Transformation: environment-specific configuration, debug off by default, testable app factory, and documented production WSGI startup.
- Dependencies: configuration work in AUD-003 and composition in AUD-004.
- Contract effect: debug behavior is disabled outside explicit development configuration; HTTP domain contracts otherwise remain unchanged.

#### AUD-009 — Order and relational integrity can be violated (DI-01, outside catalog)

- Evidence:
  - Request validation checks only that `usuario_id` is truthy and `itens` is nonempty (`controllers.py:188-206`).
  - Quantities are not required to be positive or numeric (`models.py:139-166`); a negative quantity increases stock and reduces the order total.
  - Repeated lines for one product are checked independently against the same initial stock, then can overdraw it.
  - A nonexistent user is accepted.
  - Schema has no foreign keys/check constraints (`database.py:14-53`).
- Impact: negative totals, increased stock through purchases, overselling, orphaned orders/items, and inconsistent reports.
- Transformation: structured item validation, duplicate-product aggregation, user/product existence checks inside one transaction, and compatible database constraints.
- Dependencies: AUD-006 and AUD-007; schema changes require a data-quality migration.
- Contract effect: invalid orders that can currently return 201 instead return 400; valid orders retain their 201 response.

### MEDIUM

#### AUD-010 — N+1 order retrieval (AP-08)

- Evidence: `models.py:171-233` performs one item query per order and one product-name query per item in both order-list functions.
- Impact: query count grows as `1 + orders + items`, degrading list endpoints with data volume.
- Transformation: set-based joined retrieval or bounded bulk queries, preserving missing-product fallback and response assembly.
- Dependencies: best placed in the order model created by AUD-004; otherwise independent.
- Contract effect: response shape preserved.

#### AUD-011 — Duplicated validation and serialization have diverged (AP-09)

- Evidence:
  - Product create/update validation is copied at `controllers.py:24-62` and `64-96`.
  - Create validates name length and category; update does not.
  - Product serialization is repeated at `models.py:4-41` and `285-314`.
  - User/order assembly is manually duplicated in several functions.
- Impact: the same entity accepts different invalid states depending on operation and response fields can drift.
- Transformation: shared typed validators and explicit entity serializers, retaining endpoint-specific fields.
- Dependencies: aligns with AUD-004.
- Contract effect: `PUT /produtos/<id>` newly rejects invalid name lengths and categories with 400.

#### AUD-012 — Order status behavior is inconsistent (DI-02, outside catalog)

- Evidence:
  - Any listed status may replace any other status (`controllers.py:237-252`).
  - Updating a nonexistent order still returns 200 because affected-row count is ignored (`models.py:275-283`).
  - Cancellation logs “Devolver estoque” but never restores inventory (`controllers.py:247-250`).
- Impact: false success responses, invalid lifecycle transitions, and permanently incorrect inventory after cancellation.
- Transformation: explicit state-transition policy, existence/row-count check, and atomic stock restoration on first cancellation.
- Dependencies: AUD-007 and order ownership/administrator policy from AUD-002.
- Contract effect: missing orders return 404; illegal transitions return 409; cancellation changes persistent stock as well as status.

#### AUD-013 — Internal exception details are returned to clients (SEC-02, outside catalog)

- Evidence: broad `except Exception` with `{"erro": str(e)}` throughout `controllers.py:5-292`; SQL errors returned from `app.py:77-78`; health returns details at `controllers.py:291-292`.
- Impact: database/schema/runtime details leak and malformed client input is frequently misclassified as 500.
- Transformation: centralized error mapping, structured 400 errors for malformed input, generic 500 responses, internal-only logging. The authorized SQL console may retain useful SQL errors as part of its approved admin function.
- Dependencies: centralized mapping benefits from AUD-004.
- Contract effect: malformed payloads and numeric filters become 400 instead of 500; non-admin 500 bodies no longer expose exception text.

### LOW

#### AUD-014 — Unnamed and duplicated domain constants (AP-11)

- Evidence:
  - Categories: `controllers.py:52`.
  - Status values: `controllers.py:242`.
  - Discount thresholds/rates: `models.py:256-262`.
  - Version/debug/database literals are duplicated across modules.
- Impact: policy changes can diverge and business intent is obscured.
- Transformation: named constants or domain policies while preserving current values, descending discount order, strict `>` comparisons, and rounding behavior.
- Contract effect: preserved.

#### AUD-015 — Proven unused imports (AP-12)

- Evidence: `sqlite3` is imported but unused in `models.py:2`; `os` is imported but unused in `database.py:2`. Repository-wide searches found no use.
- Impact: minor misleading coupling.
- Transformation: remove those imports after boot/static verification.
- Contract effect: preserved.

### Suspicion, not counted

`CORS(app)` applies extension defaults globally (`app.py:9`). Whether this is unsafe depends on the intended browser origins and future credential transport, neither of which is documented. Restricting origins is therefore not included as a confirmed mandatory change. It can be approved separately once allowed origins are supplied.

## 5. Full method/path contract inventory

Entity shapes observed:

- Product: `{id,nome,descricao,preco,estoque,categoria,ativo,criado_em}`
- User list/detail: `{id,nome,email,senha,tipo,criado_em}`
- Login user: `{id,nome,email,tipo}`
- Order: `{id,usuario_id,status,total,criado_em,itens:[{produto_id,produto_nome,quantidade,preco_unitario}]}`
- Common handled failure: `500 {"erro": <exception text>}` unless noted otherwise.

| Method and path | Inputs | Current response and business effect |
|---|---|---|
| `GET /` | None | 200 `{mensagem,versao,endpoints}` |
| `GET /produtos` | None | 200 `{dados:[Product],sucesso:true}` |
| `GET /produtos/busca` | Query `q`, `categoria`, `preco_min`, `preco_max` | 200 `{dados:[Product],total,sucesso:true}`; invalid numeric conversion becomes 500 |
| `GET /produtos/<int:id>` | Integer path ID | 200 `{dados:Product,sucesso:true}`; 404 `{erro,sucesso:false}` |
| `POST /produtos` | JSON `nome`, `preco`, `estoque`; optional `descricao`, `categoria` | 201 `{dados:{id},sucesso:true,mensagem}`; 400 for missing fields, negative price/stock, name length, or invalid category; inserts product |
| `PUT /produtos/<int:id>` | Full JSON `nome`, `preco`, `estoque`; optional `descricao`, `categoria` | 200 `{sucesso:true,mensagem}`; 404 if absent; 400 for missing values or negative price/stock; replaces fields |
| `DELETE /produtos/<int:id>` | Integer path ID | 200 `{sucesso:true,mensagem}` or 404; deletes even when historical items reference it |
| `GET /usuarios` | None | 200 `{dados:[User],sucesso:true}` including plaintext passwords |
| `GET /usuarios/<int:id>` | Integer path ID | 200 `{dados:User,sucesso:true}` including password; 404 `{erro}` |
| `POST /usuarios` | JSON `nome`, `email`, `senha` | 201 `{dados:{id},sucesso:true}`; 400 if missing/empty; stores plaintext; duplicate email permitted |
| `POST /login` | JSON `email`, `senha` | 200 `{dados:LoginUser,sucesso:true,mensagem}`; 401 `{erro,sucesso:false}`; issues no credential |
| `POST /pedidos` | JSON `usuario_id`, `itens:[{produto_id,quantidade}]` | 201 `{dados:{pedido_id,total},sucesso:true,mensagem}` and deducts stock; model business errors become 400 `{erro,sucesso:false}` |
| `GET /pedidos` | None | 200 `{dados:[Order],sucesso:true}` for all users |
| `GET /pedidos/usuario/<int:usuario_id>` | Integer user ID | 200 `{dados:[Order],sucesso:true}`; nonexistent user produces an empty list |
| `PUT /pedidos/<int:pedido_id>/status` | JSON `status`; allowed values `pendente`, `aprovado`, `enviado`, `entregue`, `cancelado` | 200 `{sucesso:true,mensagem}` even if order does not exist; 400 for an unlisted status |
| `GET /relatorios/vendas` | None | 200 `{dados:{total_pedidos,faturamento_bruto,desconto_aplicavel,faturamento_liquido,pedidos_pendentes,pedidos_aprovados,pedidos_cancelados,ticket_medio},sucesso:true}` |
| `GET /health` | None | 200 `{status,database,counts,versao,ambiente,db_path,debug,secret_key}`; invoking persistence can initialize/seed the DB |
| `POST /admin/reset-db` | None | 200 `{mensagem,sucesso:true}`; deletes all items, orders, products, and users; unhandled failure uses Flask’s default 500 |
| `POST /admin/query` | JSON `sql` | 400 if empty; SQL beginning with `SELECT` returns 200 `{dados:[rows],sucesso:true}`; other SQL commits and returns 200 `{mensagem,sucesso:true}`; SQL errors return 500 `{erro}` |

## 6. Proposed MVC transformation

Target boundaries:

```text
create_app/configuration
├── routes: HTTP method/path, request adaptation, response/status
├── controllers: use-case decisions and authorization outcomes
├── models/repositories: parameterized persistence and entity mapping
├── services
│   └── OrderService: order validation, transaction, stock, cancellation
├── auth middleware: token verification, identity, roles/ownership
├── database: request-scoped connection, teardown, schema/migrations
└── error mapping: client errors, not-found/conflict, safe server errors
```

Proposed domain modules: products, users/authentication, orders, reports, administration, and system/health.

Ordered transformation slices and rollback points:

1. After approval, recheck revision/status and persist this approved report.
2. Build characterization tests against a disposable SQLite file for all 19 contracts.
3. Introduce an app factory, configuration object, request-scoped connection, teardown, and production-safe startup. Roll back as one composition/config slice.
4. Parameterize every domain query. Keep `/admin/query` arbitrary but place it behind verified administrator authorization. Roll back the domain model slice without weakening console authorization.
5. Extract product routes/controller/model with existing success envelopes.
6. Extract user/auth routes/controller/model; migrate passwords, issue tokens, and remove password serialization.
7. Extract order routes/controller/model plus `OrderService`; make creation/cancellation transactional and enforce integrity.
8. Extract report, health, and administrative boundaries; make reset transactional.
9. Replace N+1 retrieval with set-based loading.
10. Centralize validation, serialization, constants, and error mapping; remove dead imports.
11. Validate real boot and all inventoried paths with disposable data, including authorized success and 401/403 denial.
12. Re-audit, record unresolved findings, and stop incomplete if validation cannot meet the approved contracts.

### Finding dependencies

| Finding | Required or material dependencies |
|---|---|
| AUD-001 | Independent for domain SQL; admin trust boundary requires AUD-002 |
| AUD-002 | AUD-003 and AUD-005 |
| AUD-003 | None; feeds authentication and safe startup |
| AUD-004 | None; architectural foundation for several later changes |
| AUD-005 | AUD-003; consumed by AUD-002 |
| AUD-006 | Prefer AUD-004 app composition |
| AUD-007 | AUD-006 and order/admin use-case boundaries from AUD-004 |
| AUD-008 | AUD-003 and AUD-004 |
| AUD-009 | AUD-006, AUD-007, and data migration |
| AUD-010 | Independent, preferably after AUD-004 |
| AUD-011 | Prefer AUD-004; its stricter update rules require explicit approval |
| AUD-012 | AUD-002 for permissions and AUD-007 for atomic stock restoration |
| AUD-013 | Prefer AUD-004 centralized mapping |
| AUD-014 | Independent |
| AUD-015 | Independent |

## 7. Intentional contract differences

All contracts not listed below are intended to retain their method, path, inputs, successful status, response envelope, and business effect.

| Affected contract | Before | Proposed after | Verification |
|---|---|---|---|
| Protected routes | Anonymous calls execute | Missing identity: 401 `{"erro":"Autenticação necessária","sucesso":false}`; insufficient role/ownership: 403 `{"erro":"Acesso negado","sucesso":false}` | Anonymous, customer, owner, and admin cases plus authorized persisted effects |
| `POST /admin/query` | Anonymous arbitrary SQL | Administrator-only arbitrary SQL; SQL capability retained | Anonymous 401, customer 403, admin `SELECT` and write both succeed |
| `POST /admin/reset-db` | Anonymous destructive reset | Administrator-only transactional reset | Denials leave data intact; admin success removes all four entity sets |
| `POST /login` | Returns user data but no credential | Same user data plus top-level signed `token` and `expires_in`; invalid/tampered/expired credentials produce 401 | Correct, wrong, tampered, and expired cases |
| `GET /usuarios`, `GET /usuarios/<id>` | Include `senha` | Omit password/hash field | Sentinel hash absent from response/logs |
| `GET /health` | Includes `secret_key`, `db_path`, and `debug` | Those three fields removed; `status`, `database`, `counts`, `versao`, and `ambiente` retained | Exact key comparison |
| SQL-backed domain routes | Quotes/SQL syntax alter statements | Values are always treated literally | Injection attempts, apostrophe round-trip, normal success |
| Malformed JSON/types and search numbers | Several paths return 500 with exception text | 400 structured client error | Missing JSON, nonnumeric range, wrong types |
| `PUT /produtos/<id>` | Does not enforce create’s name/category rules | Same name-length and category validation as create; invalid value returns 400 | Boundary lengths and every category |
| `POST /pedidos` | Accepts nonexistent users, nonpositive quantities, and duplicate-line overselling | Authenticated identity must match `usuario_id` unless admin; positive integer quantities; aggregate duplicate products; invalid order returns 400 | Negative/zero/type/duplicate/ownership tests |
| `POST /usuarios` | Duplicate emails allowed | Duplicate normalized email returns 409 | Existing/new email tests |
| `DELETE /produtos/<id>` | Can orphan historical items | Referenced product returns 409; unused product still deletes with 200 | Referenced/unreferenced cases |
| `PUT /pedidos/<id>/status` | Missing ID returns 200; any allowed value can follow any state | Missing ID 404; illegal transition 409; permitted transition 200 | State-transition matrix |
| Cancellation | Changes status only | First valid cancellation atomically restores stock; repeated/illegal cancellation does not double-restore | Stock before/after and induced rollback |
| Non-admin server errors | Return raw `str(e)` | Generic 500 body; detailed errors logged internally | Induced database failure and response inspection |
| Startup/configuration | Hardcoded secret, debug enabled, implicit schema/seed | Required production secret, debug off, explicit migration/bootstrap; no implicit production seed | Missing/configured environment and clean boot |

CORS restriction is deliberately not in this table because the required allowed-origin policy is unverified.

## 8. Migration and rollback impacts

### Data migration

Before changing an existing database:

1. Create and verify a recoverable backup. No existing database is present in this repository.
2. Inventory duplicate emails, orphaned orders/items, invalid statuses, nonpositive quantities, negative stock/totals, and repeated order-product rows.
3. Resolve anomalies under an approved retention policy before enabling constraints.
4. Hash each existing plaintext password once with scrypt in a migration transaction and record a schema/auth version.
5. Rebuild SQLite tables as needed to add foreign keys, uniqueness, and check constraints; enable `PRAGMA foreign_keys=ON` on every connection.
6. Separate schema migration from optional demonstration seed data.
7. Rotate the signing secret and invalidate any credentials issued under the exposed key.

No database operation or migration has been run.

### Rollback

- Keep a pre-migration database backup and a code revision for every coherent slice.
- Password hashing is intentionally one-way. Rollback must use code capable of verifying the new hashes or restore the protected backup; converting hashes back to plaintext is impossible and must not be attempted.
- Schema rollback should restore the verified backup rather than destructively reverse table rebuilds.
- Secret rotation invalidates old tokens; rolling code back must not reintroduce the exposed key.
- Transaction/connection/architecture slices can be reverted independently if characterization contracts remain green.
- Do not roll back authorization alone while leaving the administrative SQL console exposed.
- Cancellation/restock rollback requires restoring the data backup if migrated behavior has already changed stock.

## 9. Selectable approval scope

You may approve:

- Individual finding IDs.
- A severity level.
- One of these dependency-aware groups:

| Group | Scope |
|---|---|
| Security boundary | AUD-001, AUD-002, AUD-003, AUD-005, AUD-008, AUD-013 |
| MVC core | AUD-004, AUD-006 |
| Transaction and data integrity | AUD-007, AUD-009, AUD-012; requires MVC core |
| Query/validation quality | AUD-010, AUD-011, AUD-014, AUD-015 |
| All confirmed | AUD-001 through AUD-015 |
| Optional CORS work | Suspicion only; requires the approved origin list |

Partial approval does not approve dependencies automatically. If a selected correction requires an unselected finding, Phase 3 will remain stopped until the dependency is explicitly added.

## Approval gate

The post-approval audit report will be written to exactly:

`reports/audit-project-1.md`

Please explicitly respond with an approved scope—for example, `Approve all confirmed findings and the proposed contract differences`, or list specific finding IDs/groups and any changes to the proposed authorization, order-transition, deletion, password-migration, or SQL-console policies.

Until that explicit approval is given, the repository remains unchanged and Phase 3 will not begin.
