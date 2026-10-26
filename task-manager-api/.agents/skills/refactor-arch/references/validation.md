# Validation and evidence

## Before transformation

- verify the audited revision and approved scope;
- save the approved audit;
- record runtime/dependency versions and preexisting failures;
- copy persistent data or use a disposable database; never run a destructive seed;
- characterize every explicit method/path: input, status, response and persisted effect.
- read [regression-checks.md](regression-checks.md); use the same semantic fixtures
  on original and transformed code, separating legacy defects from regressions.

## During transformation

For each approved slice, capture the failing characterization/security test first,
the focused passing run, relevant suite result and finding ID. Normalize dynamic IDs
and timestamps without weakening assertions. Test malformed input, absent resources,
authorization and rollback where applicable.

## Completion matrix

- clean real process boot and sanitized log;
- every inventoried method/path exercised with its fixture;
- authorized success for protected endpoints plus negative access cases;
- transaction failure leaves no partial state;
- legacy database copy opens without destructive reseed;
- query-count evidence for N+1 corrections;
- response contains no password/hash/secret;
- re-audit maps each initial finding to corrected, accepted pending, or failed;
- migration and rollback commands are reproducible.
- processes started by validation are identified and stopped, including children;
- audit counts, documentation and copied skill versions match the actual run;
- final repository delivery is reproducible from only tracked files and manifests.

Static checks supplement but do not replace boot and HTTP behavior. A failed required
case keeps the result incomplete. Sanitize logs before storing evidence.
