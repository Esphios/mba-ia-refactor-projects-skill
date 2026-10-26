# Contract and runtime regression checks

Derive cases from the inspected code and approved contract. These are risk probes,
not authorization to add features or change business rules.

## Response parity

Run matching fixtures against the original and refactored application. Compare
method/path, status, response keys, types and persisted effects. Normalize only
identified dynamic fields such as generated IDs and timestamps. Cover:

- omitted, null and empty values separately; create/update may differ;
- no rows, zero totals and absent relationships; SQL SUM may return null;
- search case, wildcard/escape behavior and Unicode; replacing SQL LIKE with a
  language substring comparison can change the API;
- ordering, duplicates and list/detail serialization differences;
- exact messages where contractual, JSON encoding, 404/405 and malformed JSON;
- monetary bounds and nonfinite values; reject bool where a numeric type is needed.

## Transactions and identity

Keep read, decision and write inside the same consistency boundary. Reading status
before acquiring a transaction lock can permit double cancellation/restock even
when writes are transactional. Test simultaneous requests and repeated operations,
not only failure of a single statement. Exercise every intermediate failure in a
multi-write use case and confirm no partial state remains.

Verify current account status/role, not only signed token content, when that is the
approved policy. Test owner, other account, administrator and unauthenticated calls
with successful persisted effects as well as denial.

## Legacy credentials and dates

Inspect the actual password format. Plaintext and recognized legacy hashes may
support a controlled upgrade after successful login; a truncated/reversible
derivation may not verify a full password safely and can require explicit reset.
Never fall back to legacy verification after a modern hash fails. Test Unicode
passwords, wrong passwords, persisted upgrades, inactive accounts and expiry.

Define a configurable migration cutoff and test both sides with a controlled clock
or explicit fixture values; do not make regression tests depend on today's date.
Preserve the actual naive/aware storage and HTTP date contracts at one boundary.

## Isolated runtime

Use a disposable database and explicit fixtures. Importing the original may create
schema or seed data; run it only in the approved characterization environment.
Verify environment executables actually run before reusing virtual environments.
Install from manifests/lockfiles and record versions. Diagnose native-module,
runtime or lockfile failures before selecting the smallest compatible fix. Check
current official advisories when a dependency change is required; never blindly
apply a forced major upgrade or report an audit that was not executed.

For real boot, record command, PID, chosen port, readiness timeout and result.
Use try/finally and terminate only the process tree started by this validation.
On Windows, launch background helpers hidden and account for launcher children.
Verify shutdown before deleting fixture directories; never kill all Python/Node
processes. Record cleanup failures rather than treating HTTP success as full PASS.

Write/read source and logs with explicit UTF-8. Do not silently rewrite localized
messages when adapting scripts across shells. Preserve useful original imports
and behaviors until their callers and effects have been traced.
