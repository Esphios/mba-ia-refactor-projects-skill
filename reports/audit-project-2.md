# Phase 1/2 independent audit

## Audit header and scope

- Project: `D:\Docs\Workspace\mba-ia-workspace\desafios\refactor-projects-skill\ecommerce-api-legacy`
- Git repository: `D:\Docs\Workspace\mba-ia-workspace\desafios\refactor-projects-skill`
- Revision before and after inspection: `6d1ce6248c3e956801010a89d8bdaab48029bf30`
- Analysis date: 2026-10-22
- Skill: `refactor-arch`; SHA-256 `0b17f6fc6ae3c12100455a45c9824be0552b5dec984f9fc33578a23952bfb115`
- Repository instructions: no `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, or Copilot instruction file was found between the project and Git root.
- Independent scope: no sibling report or prior project audit was used.
- Application source inspected: **3 files, 180 lines**
  - `src/app.js`: 14 lines
  - `src/AppManager.js`: 141 lines
  - `src/utils.js`: 25 lines
- Also inspected completely or structurally:
  - `package.json`
  - all 2,288 lines/192 package entries represented by `package-lock.json`
  - `README.md`
  - `api.http`
  - the skill and all Phase 1/2 references required for confirmed transformations
- Excluded from application-source count:
  - the 7 untracked `.agents/skills/refactor-arch/**` instruction/reference files;
  - the four manifest/document/request files above;
  - `.git`;
  - `node_modules`, which does not exist;
  - generated output, caches, databases, tests, and migrations, none of which exist in this project.

### Exact working-tree scope

All seven tracked application files are unchanged:

- `README.md`
- `api.http`
- `package.json`
- `package-lock.json`
- `src/app.js`
- `src/AppManager.js`
- `src/utils.js`

The only project-local dirty paths are these pre-existing untracked audit-skill files:

- `.agents/skills/refactor-arch/SKILL.md`
- `.agents/skills/refactor-arch/references/anti-patterns.md`
- `.agents/skills/refactor-arch/references/audit-report-template.md`
- `.agents/skills/refactor-arch/references/mvc-guidelines.md`
- `.agents/skills/refactor-arch/references/project-analysis.md`
- `.agents/skills/refactor-arch/references/refactoring-playbook.md`
- `.agents/skills/refactor-arch/references/validation.md`

The repository is also dirty outside this project: root `.gitignore`/`README.md`, `../code-smells-project/**`, and `../reports/**` contain existing changes or untracked files. They were out of scope and untouched.

## Phase 1 — project analysis

### Stack and version confidence

| Category | Evidence |
|---|---|
| Language | JavaScript/CommonJS |
| Framework | Express |
| Persistence | Direct callback-based `sqlite3`; one in-memory `:memory:` database |
| Declared application version | `1.0.0` |
| Declared dependencies | Express `^4.18.2`; sqlite3 `^5.1.6` |
| Lockfile resolutions | Express `4.22.1`; sqlite3 `5.1.7`; npm lockfile v3, 192 package entries |
| Verified local toolchain | Node `v24.12.0`; npm `11.19.1` |
| Runtime dependency versions | **Unverified**: `node_modules` is absent and no installation or application import occurred |
| SQLite engine/native binary | **Unverified** |
| Deprecation status | **Unverified**; no AP-10 finding is asserted from lock metadata alone |

### Domain, persistence, and entry points

The domain is an LMS/e-commerce checkout:

- users;
- courses;
- enrollments;
- payments;
- checkout audit entries;
- administrative financial reporting;
- user deletion.

Persistence is an automatically seeded, non-durable SQLite in-memory database. Five tables are created in `src/AppManager.js:12-16`; seed data is inserted at `18-21`. No foreign keys, uniqueness constraints, migration mechanism, or durable database path exists.

Entry and composition flow:

1. npm `start` invokes `node src/app.js`.
2. `src/app.js:5-10` creates Express, JSON middleware, one `AppManager`, schedules database initialization, and registers routes.
3. `src/app.js:12-14` immediately starts listening.
4. `AppManager` owns schema/seeds, all SQL, checkout policy, reporting, deletion, response construction, and route registration.
5. `utils.js` owns hardcoded configuration, a process-global cache, logging, and password transformation.

### Current responsibility/request map

- `POST /api/checkout`
  - route and request adaptation: `src/AppManager.js:28-35`
  - course/user lookup: `37-41`
  - simulated card decision: `43-48`
  - user/enrollment/payment/audit writes: `50-72`
  - cache/log response: `57-60`
- `GET /api/admin/financial-report`
  - route, report policy, nested SQL, aggregation, serialization: `80-129`
- `DELETE /api/users/:id`
  - route, direct SQL, response: `131-137`

There are no explicit Model, Controller, or separate Route layers despite all three responsibilities being present.

## Existing HTTP contract inventory

Automatic `HEAD` and `OPTIONS` are excluded. Exact explicit endpoint count: **3**.

| Method/path | Input | Current reachable behavior |
|---|---|---|
| `POST /api/checkout` | JSON keys `usr`, `eml`, optional `pwd`, `c_id`, `card` | Missing truthy `usr`/`eml`/`c_id`/`card`: `400 "Bad Request"`. Missing/inactive course—or course query error—`404 "Curso não encontrado"`. User lookup error: `500 "Erro DB"`. Existing email ignores password and supplied name. New user accepts missing password and substitutes `123456`. Card string beginning `4` is paid; every other string is denied. Denial: `400 "Pagamento recusado"`, but a newly created user remains. Enrollment failure: `500 "Erro Matrícula"`. Payment failure: `500 "Erro Pagamento"`. Audit failure is ignored. Success: `200 {"msg":"Sucesso","enrollment_id":<id>}`. Non-string `card` can throw at `startsWith`. |
| `GET /api/admin/financial-report` | None | Public, unauthenticated `200` JSON array. Each item is `{course,revenue,students}`; each student is `{student,paid}`. Revenue includes only `PAID`; `paid` reports the payment amount regardless of status. Missing users become `"Unknown"` and missing payments `0`. Only the initial course-query error has an explicit `500`; nested query errors can throw, stall, or produce incomplete output. Completion order is nondeterministic. |
| `DELETE /api/users/:id` | Path `id` | Public and unauthenticated. Executes parameterized deletion, ignores the database error and affected-row count, and always returns `200 "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`. Enrollments/payments are retained as orphans. |

## Severity summary

| Severity | Count |
|---|---:|
| CRITICAL | 2 |
| HIGH | 4 |
| MEDIUM | 1 |
| LOW | 2 |
| **Total** | **9** |

## Confirmed findings

### F-01 — CRITICAL — AP-02: hardcoded/exposed credentials and sensitive log disclosure

- Evidence:
  - `src/utils.js:1-6`: hardcoded database username/password, live-looking payment key, SMTP user, and port.
  - `src/AppManager.js:45`: logs the complete submitted card value and payment key together.
  - `api.http:7-13,19-25`: demonstrates that full card values reach this path.
- Reachable scenario: any checkout request reaches line 45 before the payment decision and emits the supplied full card plus configured key.
- Impact: credential extraction from source, repository history, console or centralized logs; full payment-card disclosure; rotation and audit exposure.
- Severity basis: the challenge rubric explicitly classifies exposed/hardcoded credentials as CRITICAL. Whether the embedded strings remain operationally valid is not verified.
- Transformation:
  - load secrets and environment-specific settings from validated external configuration;
  - fail startup when required secrets are absent;
  - never log a card, password, hash, or gateway secret;
  - log only a correlation ID and non-sensitive outcome;
  - rotate any credential that may have been deployed.
- Verification:
  - missing/configured startup tests;
  - capture logs with sentinel card/key values and assert neither appears;
  - scan responses and source;
  - verify normal checkout after configuration.
- Dependencies: architectural composition from F-02 simplifies injected configuration; credential rotation is an external operational dependency.
- Contract effect: HTTP success/error shapes can be preserved; startup requirements and log output intentionally change.

### F-02 — CRITICAL — AP-03: God Class combining database, complex business logic, and routing

- Evidence:
  - `src/AppManager.js:4-138`: one class owns the database object, schema, seeds, three routes, validation, payment decision, checkout orchestration, financial aggregation, deletion, SQL, error/status mapping, and serialization.
  - `src/app.js:8-10`: the same singleton is initialized and handed the Express application.
- Reachable scenario: every exposed request passes through this unit and directly couples HTTP behavior to SQLite callbacks and domain decisions.
- Impact: unsafe change radius, untestable business rules, security checks duplicated or omitted, transaction ownership obscured, and startup/persistence tightly coupled.
- Severity basis: it meets the challenge’s explicit CRITICAL God Class rule—database, complex business logic, and routing coexist in one unit.
- Transformation: establish explicit Routes, Controllers, and Models/repositories; use services only for checkout transactions, authentication, and user-lifecycle orchestration.
- Verification: request-to-response characterization for all three endpoints, unit tests at the new boundaries, dependency-direction checks, and real boot/HTTP verification only in approved Phase 3.
- Dependencies: foundation for F-04 through F-08.
- Contract effect: structural extraction itself preserves methods, paths, public keys, status codes, shapes, and business effects; separately approved security/reliability differences are listed below.

Input validation belongs at the route boundary. The current truthiness-only check at `src/AppManager.js:29-35` does not validate types, email, integer course ID, password, or card shape; missing passwords are defaulted at line 68 and non-string cards can throw at line 46. That confirmed behavior is part of this misplaced-responsibility finding, not an invented AP-09 duplication finding.

### F-03 — HIGH — AP-04: plaintext and reversibly weak password storage

- Evidence:
  - `src/AppManager.js:18`: seed password stored as plaintext `"123"`.
  - `src/AppManager.js:68-69`: missing password becomes `"123456"` and is passed through `badCrypto`.
  - `src/utils.js:17-23`: deterministic repeated Base64 fragments are truncated to ten characters; there is no salt or password KDF.
- Reachable scenario: creation during checkout stores a cheaply derived value; the seeded account is plaintext.
- Impact: rapid password recovery, identical values for identical passwords, account compromise, and unsafe credential migration.
- Transformation: require a password for account creation, use a salted memory-hard password KDF supported by the chosen runtime, use constant-time verification, and support an explicit one-time legacy upgrade path only where the old representation can be identified.
- Verification: unique salts, correct/wrong password, legacy upgrade, missing password, disabled user, and absence of password/hash in logs/responses.
- Dependencies: F-01 for signing/configuration secrets; F-02 for auth/model boundaries; F-04 for meaningful verification.
- Contract effect: missing passwords cease to be silently defaulted; existing-account checkouts must verify identity.

### F-04 — HIGH — AP-05: missing authentication and authorization

- Evidence:
  - `src/AppManager.js:80-129`: an `admin` financial route has no authentication or role check.
  - `src/AppManager.js:131-137`: destructive user deletion has no identity, role, or ownership check.
  - `src/AppManager.js:40,73-75`: an existing account is selected by email and its password is never checked.
- Reachable scenario:
  - anyone can retrieve financial/student reporting;
  - anyone can delete any user ID;
  - anyone knowing an email can attach a paid enrollment to that account.
- Impact: privacy breach, unauthorized destructive action, account misuse, and loss of accountability.
- Transformation:
  - add verified, expiring authentication;
  - reload current user active state/role during authentication;
  - require administrator authorization for the financial report;
  - require self-or-administrator authorization for the user lifecycle endpoint;
  - require existing-account authentication during checkout;
  - retain authorized success flows, not merely denial middleware.
- Verification: anonymous `401`, authenticated unauthorized `403`, expired/tampered credential `401`, ordinary-user ownership success, administrator success, and persisted authorized effects.
- Dependencies: F-01, F-02, and F-03. The deletion portion also depends on F-06 and explicit approval of the retention policy below.
- Contract effect: intentional `401/403` responses and a new authentication mechanism/endpoint; legitimate authorized operations remain available.

### F-05 — HIGH — AP-06: shared mutable database/cache lifecycle

- Evidence:
  - `src/AppManager.js:5-8` creates one long-lived SQLite connection.
  - `src/app.js:8-10` shares that manager/connection across all requests.
  - `src/utils.js:9-15` maintains an unbounded mutable process-global cache.
- Reachable scenario: concurrent requests share one callback connection and cache; future transaction statements could interleave unless the whole use case is serialized.
- Impact: transaction interference, unpredictable concurrency, resource lifecycle leaks, unbounded process memory, and test contamination.
- Transformation: move connection ownership to an explicit database adapter, serialize complete SQLite transactions, expose deterministic close/readiness behavior, and inject a bounded cache or remove it if characterization proves it has no required consumer.
- Verification: concurrent checkout tests, failure rollback, cache isolation/bounds, and clean shutdown.
- Dependencies: F-02; transaction behavior is coupled to F-06.
- Contract effect: intended HTTP preservation; process lifecycle and internal cache behavior change.

### F-06 — HIGH — AP-07: non-atomic writes and missing rollback/error handling

- Evidence:
  - `src/AppManager.js:50-63`: enrollment, payment, and audit are independent statements with no transaction.
  - `src/AppManager.js:66-72`: a user is inserted before payment denial or later failure.
  - `src/AppManager.js:57-61`: audit insertion errors are ignored and success is still returned.
  - `src/AppManager.js:133-135`: deletion errors are ignored and success is always reported.
- Reachable scenario:
  - a denied new-user checkout leaves a user;
  - payment failure leaves an enrollment;
  - audit failure still yields success;
  - delete failure still reports deletion.
- Impact: orphaned or misleading records, incorrect financial/audit history, and false successful responses.
- Transformation:
  - validate payment outcome before writes where possible;
  - execute new-user creation, enrollment, payment, and audit in one serialized transaction;
  - roll back every write on failure;
  - centralize error translation;
  - check deletion result and preserve financial references through the approved policy.
- Verification: injected failure at every statement, zero residual rows after rollback, refusal leaves no new account/enrollment, successful checkout persists all rows, and deletion errors return failure.
- Dependencies: F-02 and F-05; user lifecycle portion depends on F-04.
- Contract effect: failed/denied operations stop leaving side effects; audit/delete failures stop returning false success.

### F-07 — MEDIUM — AP-08: N+1 financial reporting and nested error loss

- Evidence: `src/AppManager.js:83-127`.
  - One course query.
  - One enrollment query per course.
  - Two queries per enrollment, for user and payment.
  - Query growth is `1 + C + 2E`.
  - Errors at lines 92, 104, and 106 are ignored before dereferencing results.
- Reachable scenario: report latency and DB work grow linearly with courses and enrollments; a nested query error may throw, hang, or silently distort output.
- Impact: degraded administrative reporting, availability risk, inaccurate revenue/student results.
- Transformation: use bounded set-based queries/joins, aggregate deliberately to avoid revenue multiplication, and serialize the exact existing response shape in a report model/controller.
- Verification: empty data, multiple courses/enrollments, missing user/payment, paid/denied payments, forced query errors, and constant SELECT count at 1 versus 20 enrollments.
- Dependencies: F-02; benefits from F-05.
- Contract effect: authorized success shape remains `{course,revenue,students}`; deterministic ordering and proper `500` errors are intentional clarifications.

### F-08 — LOW — AP-11: unexplained payment/default-password magic values

- Evidence:
  - `src/AppManager.js:45-48`: a card beginning with literal `"4"` means `PAID`; every other prefix means `DENIED`.
  - `src/AppManager.js:68`: literal fallback password `"123456"`.
- Reachable scenario: all checkouts depend on these embedded policies.
- Impact: payment behavior is difficult to distinguish from a real gateway rule, and insecure fallback behavior is easy to retain accidentally.
- Transformation: preserve the demonstrated payment simulation behind a named gateway abstraction/test fake; remove the fallback password as part of F-03.
- Verification: prefix-4 and non-prefix-4 characterization plus missing-password validation.
- Dependencies: F-02 and F-03.
- Contract effect: the simulated payment decision remains unchanged unless separately approved; missing-password behavior changes.

### F-09 — LOW — AP-12: opaque internal names and proven dead code

- Evidence:
  - `src/AppManager.js:29-33`: internal variables `u`, `e`, `p`, `cid`, `cc`.
  - `src/utils.js:10,25` and `src/AppManager.js:2`: `totalRevenue` is declared, exported, and imported but never read.
  - Repository-wide source search found no other consumer.
- Reachable scenario: every checkout executes opaque mapping; dead state is initialized at boot.
- Impact: maintenance ambiguity and misleading indication of financial state.
- Transformation: use descriptive internal names, retain public keys `usr`, `eml`, `pwd`, `c_id`, and `card`, and remove `totalRevenue` after characterization.
- Verification: source/caller search and unchanged request mapping.
- Dependencies: best applied after F-02 extraction to avoid conflicts.
- Contract effect: preserved.

## Catalog-family disposition

| Family | Result |
|---|---|
| AP-01 SQL injection | No finding. Every request-derived SQL value uses placeholders. Literal schema/seed SQL is not untrusted input. |
| AP-02 exposed secrets | Confirmed F-01. |
| AP-03 God Class | Confirmed F-02. |
| AP-04 insecure passwords/tokens | Confirmed F-03. No tokens currently exist. |
| AP-05 missing authorization | Confirmed F-04. |
| AP-06 global/shared connection | Confirmed F-05. |
| AP-07 partial writes | Confirmed F-06. |
| AP-08 N+1 | Confirmed F-07. |
| AP-09 duplicated validation/serialization | No duplicate implementation exists; incomplete boundary validation is addressed under F-02 without manufacturing AP-09. |
| AP-10 deprecated API | No confirmed finding; installed dependency/native runtime was not available and no official deprecation verification was performed. |
| AP-11 magic values | Confirmed F-08. |
| AP-12 opaque names/dead code | Confirmed F-09. |

## Suspicions, not counted as findings

- **Startup readiness:** `src/app.js:8-12` listens without an initialization completion/error contract, while `initDb()` ignores all schema/seed errors. SQLite’s same-connection queue may preserve statement ordering, so an actual pre-schema request failure is not asserted without runtime testing. The target design must nevertheless listen only after successful readiness.
- **Credential validity:** the embedded strings look production-oriented, but their current external validity and required rotation scope cannot be verified statically.
- **Dependency maintenance/security:** lockfile metadata was inspected, but no online advisory/deprecation audit or installed-package execution occurred.
- **Global cache growth:** mutation is confirmed; actual production growth is unverified because only checkout writes and no reader exists.

## Target MVC architecture

```text
src/
  app.js                    testable Express composition; no listen
  server.js                 configuration, DB readiness, listen, shutdown
  config/
    index.js                validated external configuration
  routes/
    authRoutes.js
    checkoutRoutes.js
    adminRoutes.js
    userRoutes.js
  controllers/
    authController.js
    checkoutController.js
    reportController.js
    userController.js
  models/
    userModel.js
    courseModel.js
    enrollmentModel.js
    paymentModel.js
    auditModel.js
    financialReportModel.js
  services/
    authService.js          authentication/token orchestration
    checkoutService.js      payment decision + atomic transaction
    userLifecycleService.js authorization + retention transaction
  middleware/
    authenticate.js
    authorize.js
    errorHandler.js
  db/
    connection.js
    schema.js
  validation/
    checkoutInput.js
```

Routes own method/path and request adaptation. Controllers choose application/HTTP outcomes. Models own SQL. Services exist only for meaningful authentication, transaction, or lifecycle orchestration.

## Ordered transformation slices and rollback points

1. **Characterization baseline after approval**
   - Capture all three current HTTP contracts using disposable data.
   - Rollback point: no source change.

2. **External configuration and log redaction — F-01**
   - Introduce validated configuration; redact card/key.
   - Rollback: revert code/config contract. Secret rotation itself is not reversible.

3. **Boot/composition and MVC foundation — F-02, F-05**
   - Separate testable app from server startup; add readiness/close lifecycle; extract routes/controllers/models without changing HTTP behavior.
   - Rollback: module-by-module revert while the original route characterization remains green.

4. **Checkout validation and transaction — F-06 plus relevant F-08**
   - Centralize input adaptation, serialize one transaction, roll back all rows, preserve payment simulation.
   - Rollback: revert the slice and restore the pre-slice disposable database snapshot.

5. **Password/authentication foundation — F-03**
   - Strong salted hashing, login/token flow, active status and role.
   - Rollback: code rollback plus pre-migration backup. New password hashes cannot safely be reversed.

6. **Authorization — F-04**
   - Protect report, deletion, and existing-account checkout; prove authorized success and denial.
   - Rollback: revert middleware/policy as one slice, without reverting password storage.

7. **User lifecycle and financial retention — F-04/F-06**
   - Implement authorized deactivation/anonymization while retaining financial records.
   - Rollback: code/schema rollback from backup. Completed anonymization may be intentionally irreversible.

8. **Set-based reporting/error handling — F-07**
   - Replace N+1 callbacks, preserve shape, establish deterministic ordering.
   - Rollback: restore prior report model/controller only.

9. **Names/dead code — F-09**
   - Rename internals and remove proven-unused state.
   - Rollback: direct source revert.

Each slice requires a failing/characterizing test first and focused/regression verification in Phase 3.

## Complete intentional contract-difference table

| Method/path/surface | Before | Proposed after | Reason/tests |
|---|---|---|---|
| Process startup | Listens immediately; embedded config; initialization errors ignored | Validate configuration and database readiness before listening; fail startup on missing secret/schema error | F-01/F-02; missing/configured startup and induced schema failure |
| Logs | Full card and gateway key | Correlation ID and non-sensitive outcome only | F-01; sentinel log capture |
| `POST /api/auth/login` | Absent | New endpoint issuing an expiring verified credential after password check | Required to preserve authorized admin/user flows; correct/wrong/expired/tampered tests |
| `POST /api/checkout`, public keys | `usr`, `eml`, `pwd`, `c_id`, `card` | Same keys retained | Contract preservation |
| Checkout missing password | Defaulted to `123456` | `400` validation error for new account; existing account requires authentication/verification | F-03/F-04; boundary tests |
| Checkout malformed types/email/course ID/card | May pass truthiness or throw/default to Express error | Stable `400` validation response | F-02; type/boundary tests |
| Checkout existing email | Password ignored | Invalid/missing identity returns `401`; verified user may proceed | F-04; ownership tests |
| Checkout course query failure | `404` | `500`; true absent/inactive course remains `404` | Correct error semantics |
| Checkout denial | `400 "Pagamento recusado"` but may leave a new user | Same external denial status/body, no retained user/enrollment/payment | F-06 rollback test |
| Checkout write/audit failure | Partial rows or false `200` | `500` and complete rollback | F-06 induced failures |
| Checkout success | `200 {"msg":"Sucesso","enrollment_id":id}` | Preserved | Success regression |
| `GET /api/admin/financial-report`, anonymous | Public `200` | `401` | F-04 |
| Report, authenticated non-admin | Public `200` | `403` | F-04 |
| Report, administrator | `200` current array shape | `200` same field shape, deterministic order | Authorized success and ordering tests |
| Report nested DB error | Throw, stall, or partial result | Stable `500` | F-07 failure tests |
| `DELETE /api/users/:id`, anonymous | Always public `200` | `401` | F-04 |
| Delete authenticated but unauthorized | Always public `200` | `403` | F-04 |
| Delete missing user | False `200` | `404` | Correct result handling |
| Delete DB failure | False `200` | `500` | F-06 |
| Authorized delete/deactivate | Hard-deletes user and leaves financial orphans; misleading text response | Deactivate/anonymize eligible personal data, preserve linked financial history, return truthful `200` lifecycle result | Explicit human approval required; retention/integrity tests |
| Internal password storage | Plaintext/deterministic 10-character transform | Salted password KDF with explicit legacy handling | F-03 |
| Report query behavior | `1 + C + 2E` SELECTs | Bounded set-based retrieval | F-07; query-count test |
| Payment simulation | Prefix `4` means paid | Preserved behind named abstraction | F-08 |

Error bodies should be defined during characterization. The table approves semantic changes, not arbitrary response-envelope churn.

## Migration, retention, and rollback impacts

The current database is in memory and is recreated and seeded on every boot, so there is no repository-held durable data to migrate. Any deployed durable variant must nevertheless be treated separately.

Proposed forward-compatible schema additions:

- user role;
- active/deactivated status;
- `deleted_at`/`anonymized_at`;
- identifiable password-hash format/version;
- optional audit actor/correlation metadata;
- foreign-key/index strategy that does not cascade-delete financial records.

### Proposed deletion policy — explicit human decision required

Default behavior must preserve financial history:

- authorize self-service or administrator lifecycle action;
- deactivate authentication immediately;
- anonymize personal fields when legally appropriate;
- retain the stable user surrogate needed by enrollments, payments, and audit history;
- never cascade-delete enrollments or payments;
- allow physical user-row deletion only when no retained financial/legal relationship exists, or through a separately approved exceptional purge policy.

This preserves legitimate deletion/deactivation while preventing orphaned financial history. **Approval of this policy is required before implementation.**

For any durable deployment:

1. take and verify a backup;
2. migrate additively in a transaction;
3. classify existing plaintext/legacy hashes explicitly;
4. do not drop old columns in the first release;
5. verify enrollment/payment totals before and after;
6. keep a code-and-schema rollback plan;
7. recognize that credential rotation, password upgrades, and completed anonymization may be intentionally irreversible.

No existing database may be seeded or migrated during this audit.

## Selectable scope and dependency groups

Findings can be selected individually or by severity, subject to these dependencies:

- **G1 — Configuration/security:** F-01. Independent for redaction; auth signing configuration is also required by G3.
- **G2 — MVC/lifecycle foundation:** F-02 + F-05. Required by G3–G5.
- **G3 — Identity and authorization:** F-03 + F-04 + F-01 + G2.
- **G4 — Checkout integrity:** F-06 checkout portion + G2; F-08’s default-password portion also requires F-03.
- **G5 — Financial reporting:** F-07 + F-02.
- **G6 — User deletion/retention:** F-04 deletion portion + F-06 error/transaction portion + G2 + explicit approval of the retention policy.
- **G7 — Cleanup:** F-09 and the payment-naming part of F-08; best applied after affected structural slices.

Severity selections:

- CRITICAL: F-01, F-02.
- HIGH: F-03–F-06, with the dependencies above.
- MEDIUM: F-07, requiring F-02.
- LOW: F-08–F-09, with their noted dependencies.
- Full remediation: F-01–F-09 and the proposed deletion policy.

Partial approval remains partial and does not approve required dependencies automatically.

## Approval gate

After approval, the exact report destination will be:

`D:\Docs\Workspace\mba-ia-workspace\desafios\refactor-projects-skill\reports\audit-project-2.md`

Do you explicitly approve this Phase 1/2 audit, its intentional contract differences, the financial-history-preserving deletion/deactivation policy, and which finding/dependency groups should enter Phase 3?

**No files were changed or created. The report was not written. The application was not imported or started, no dependency was installed, and no database, seed, migration, or other runtime/database action occurred.**

## Authorization and final retention decision
User authorization: "ignore as aprovações por enquanto. continue até o fim." This authorizes all nine finding groups and the listed safety contract differences. Final policy: physically delete a user without relationships; deactivate users with enrollments/payments, preserving all financial history. No automatic anonymization. This overrides the proposed anonymization option above. Archived before code modification on 2026-10-22.


Independent raw response: [phase 1/2 evidence](evidence/audit-project-2-phase-1-2.md). Original characterization: [baseline log](evidence/project-2-baseline.log). Final execution: [validation report](validation-project-2.md).
