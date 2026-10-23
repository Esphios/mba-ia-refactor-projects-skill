# Validation — project 1 (Flask e-commerce)

## Validated state

- Original revision: `6d1ce6248c3e956801010a89d8bdaab48029bf30`.
- Approved audit: [audit-project-1.md](audit-project-1.md).
- Refactored working-tree source manifest SHA256:
  `7531e345dba94f81239d0d02c3ee6727b923924b4da49579282f8fbdb7cd96d4`.
- Runtime: Python 3.12.10, Flask 3.1.1, Flask-CORS 5.0.1,
  pytest 8.4.2, SQLite 3.49.1.
- Validation date: 2026-10-22.

The manifest is [project-1-source-manifest.txt](evidence/project-1-source-manifest.txt).
It excludes the virtual environment, caches and disposable databases. The code is
still in the delivery worktree, so this content hash identifies the validated
state before the final delivery commit.

## Results

| Check | Result | Evidence |
|---|---:|---|
| Isolated automated suite | PASS — 43 tests | [project-1-final-pytest.txt](evidence/project-1-final-pytest.txt) |
| All 19 method/path pairs against a real Flask process | PASS — 19/19 | [project-1-http-matrix.jsonl](evidence/project-1-http-matrix.jsonl) |
| Real boot with debug disabled and sanitized health | PASS | [project-1-real-boot.txt](evidence/project-1-real-boot.txt) |
| Existing legacy-schema database and plaintext-password upgrade | PASS | `test_existing_legacy_database_opens_without_data_loss` in the suite log |
| Runtime credential literals, debug enablement and SQL in routes | none found | [project-1-static-reaudit.txt](evidence/project-1-static-reaudit.txt) |
| Import of app/MVC packages with external configuration | PASS | `imports-ok` observed with disposable `SECRET_KEY` and `DATABASE` |

The real-process matrix uses public calls where intended and valid owner/admin
tokens elsewhere. It creates and logs in a new user, logs in a legacy seeded
user, exercises a customer denial on the SQL console, creates/updates/deletes a
product, creates and advances an order, reads both order views and the sales
report, checks sanitized health, executes the approved admin SQL operation, and
finishes with the authorized reset.

## Re-audit of approved findings

| Finding | Result | Verification |
|---|---|---|
| AUD-001 SQL injection | resolved | Domain statements use bound parameters; injection tests pass. Arbitrary SQL remains only in the approved administrator console. |
| AUD-002 missing authorization | resolved | Signed identity, owner/admin guards and 401/403 cases cover protected contracts. |
| AUD-003 embedded secrets and disclosure | resolved | `SECRET_KEY` and demo passwords are required external values; health omits secret, path and debug fields. Seed refuses missing password variables. |
| AUD-004 concentrated responsibilities | resolved | Composition, routes, controllers, services and per-domain models are separate; largest domain module is 95 lines. |
| AUD-005 plaintext passwords and fake token | resolved | New passwords use scrypt; successful legacy login upgrades once; signed tokens expire and reject tampering. |
| AUD-006 global connection | resolved | SQLite connection is request/app-context scoped through Flask `g` and closed at teardown. |
| AUD-007 missing rollback | resolved | Order creation/status and reset own explicit transactions with rollback tests. |
| AUD-008 exposed debugger | resolved | Debug defaults to false and the documented host defaults to loopback. |
| AUD-009 relational/order integrity | resolved | Foreign keys are enabled; email uniqueness, positive integer quantities, duplicate aggregation, existence and guarded stock updates are tested. |
| AUD-010 N+1 reads | resolved | Order hydration uses two bounded data queries; the test allows one additional constant authentication query. |
| AUD-011 duplicated validation/serialization | resolved | Shared product validation and explicit serializers serve both create/update and user views. |
| AUD-012 inconsistent order status | resolved | Explicit transition map, 404/409 outcomes and one-time atomic restock are tested. |
| AUD-013 raw internal errors | resolved | Central handlers return generic 500 bodies; client input maps to 400/404/409 as appropriate. |
| AUD-014 unnamed constants | resolved | Categories, transitions and discount tiers are named domain constants; boundary behavior is tested. |
| AUD-015 dead imports | resolved | The audited unused imports disappeared with the module split; compile/import checks pass. |

No approved finding remains open. The separately documented CORS suspicion remains
outside the approved scope because no allowed-origin policy was supplied.

## Contracts and regression coverage

The route inventory remains 19 explicit method/path pairs. Successful response
envelopes are preserved except for the approved additions/removals. The suite
also proves:

- unauthorized and wrong-owner requests do not count as functional success;
- admin and owner success paths perform their intended effects;
- malformed inputs, duplicate email, referenced-product deletion and illegal
  transitions return their approved errors;
- induced item failure rolls back order and stock;
- cancellation restores stock exactly once;
- discounts retain strict legacy thresholds;
- user and health responses contain no password, hash or secret;
- legacy and new-password logins both succeed.

## Migration and rollback

Production boot no longer creates or seeds the database. Initialize a new empty
database with `flask --app app init-db`. Optional demo seed requires all three
`DEMO_*_PASSWORD` variables and is never invoked automatically.

Before pointing the refactored app at an existing database, make a verified copy
and check duplicate case-insensitive emails. `init-db` adds the unique email
index and will stop on conflicting legacy data rather than silently discard it.
The app can open the legacy table layout and upgrades a plaintext password only
after a successful login. That hash conversion is one-way.

Rollback consists of restoring the pre-migration database copy and the matching
code revision. If any passwords have already been upgraded, older code that only
compares plaintext cannot authenticate them; use the protected database backup
or retain hash-aware authentication during code rollback. Secret rotation
invalidates issued tokens by design.

## Commands

From `code-smells-project`:

```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m flask --app app init-db
python -m flask --app app seed-demo
python app.py
python tests/run_http_matrix.py
```

All database validation used disposable files. The validation database was
removed after the run; no repository database was modified.


## Final integration review — 22/10/2026

The final suite has 43 passing tests. New regressions were demonstrated RED and
fixed before this claim: [Unicode/cutoff](evidence/project-1-legacy-cutoff-red.log),
[concurrent cancellation](evidence/project-1-concurrency-red.log),
[nonfinite/overflow money](evidence/project-1-money-red.log),
[HTTP client errors](evidence/project-1-client-errors-red.log), and
[empty sales counts](evidence/project-1-empty-report-red.log).
The final suite log linked above covers every correction.

Status changes acquire BEGIN IMMEDIATE before reading/revalidating the order;
two concurrent cancellations now produce one success and one conflict, restoring
stock once. Prices and order totals reject nonfinite values without writes.
Empty reports preserve numeric zero counts. HTTP404/405 stay client errors and
malformed login/status values return400. Legacy Unicode passwords upgrade using
UTF-8 constant-time comparison. Production plaintext fallback ends at
LEGACY_PASSWORD_CUTOFF (default2027-01-01UTC); disposable fixtures explicitly use
2099 only to exercise migration independently of the calendar.

Real boot and the 19-contract matrix are repeated by the checkout reproduction
command; its integration log is recorded in the delivery evidence. These fixes
preserve the approved contracts and make the original validation stronger.

Final source commit: `7708f87b90b516a7203c3acaa26a8941b9e24740`. EOF-only cleanup after the source manifest in the re-audit did not alter behavior; this refreshed manifest identifies exact local bytes.

## Clean checkout reproduction

Revision `7100f0224a5442167cb50c2816ff5682054d0016` was cloned without existing environments; fresh pip/npm installs, all three suites and all real HTTP matrices passed. Project1 suite: 43 tests passed. [Complete reproduction log](evidence/clean-checkout-reproduction.log), [checkout/result record](evidence/clean-checkout.json), [17 validator tests](evidence/clean-validator-tests.log). The checkout remained Git-clean after execution.
