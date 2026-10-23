# Integration review — 22/10/2026

Plan: openspec/changes/deliver-refactor-arch-skill/tasks.md (local planning root).
Execution branch: work/deliver-refactor-arch; original revision6d1ce6248c3e956801010a89d8bdaab48029bf30.

## Rulings and scope

- User explicitly authorized continuation without approval pauses: “ignore as aprovações por enquanto. continue até o fim.” Audit records preserve this session exception; package gate remains unchanged.
- LMS login and self/admin lifecycle preserve authorized operations; physically delete only unlinked users, deactivate linked users, preserve all enrollments/payments, no automatic anonymization.
- sqlite3 major upgrade5→6 is necessary to remove observed critical installation-chain vulnerabilities, not structural preference. Node24 satisfies>=20.17; npm ci, tests, boot and audit0 verify compatibility.
- Existing checkpoint/branch and user's .gitignore intent retained. No destructive reset, existing DB seed, merge to upstream, email or external payment.
- Frozen skill and raw evidence use .gitattributes -text to preserve exact hashes despite Windows core.autocrlf. Normal sources keep existing Git line-ending policy; local precommit manifests and clean-checkout commit identity serve different scopes.

## Independent review and fixes

A fresh-context whole-delivery reviewer inspected code/tests/specs, no source mutations. Important findings: P1 stale cancellation read, nonfinite money, calendar-dependent test fixtures. Root reproduced each applicable failure, moved status read inside BEGIN IMMEDIATE, rejected nonfinite price/total, configured disposable migration fixtures2099 while production fallback expires2027. Minor client HTTP/type errors also fixed, none deferred. UTF8 legacy password regression reproduced and corrected. P1 suite43 tests passed after those fixes.

Second skill re-audit found empty P1 status-count nulls, P3 SQL LIKE/default-description regressions and later mojibake introduced by a Windows default-encoding edit. Implementers reproduced and corrected them with focused RED/GREEN cases; source manifests refreshed. The independent re-audit records these discoveries rather than claiming no findings throughout. Final clean-checkout suite will verify the complete state including latest Unicode correction.

Evidence of P1 RED runs: project-1-concurrency-red.log, project-1-money-red.log, project-1-client-errors-red.log, project-1-legacy-cutoff-red.log, project-1-empty-report-red.log. Final P1 suite project-1-final-pytest.txt43/43. P2 suite13/13 and real HTTP35 cases, audit0; P3 prior full68/68 plus new Unicode focused1/1; all69 require final clean-checkout run. No ignored baseline failure is presented as final passing evidence.

No review finding is deliberately deferred. Separate deployment choices (WSGI, CORS origins, rate limiting, secret rotation in an unaccessed deployment) remain documented operational limits, not completed deployment actions. Review excluded authorship proof, external production infrastructure and statistics; root handles file/remote/clean reproduction checks separately.

Final clean-checkout verification: all125 application tests +17 validator tests pass, three real boots,44 original contracts + LMS login. Latest Unicode fix included in full69-test P3 run. Source/skill/script tree did not change after tested revision7100f02; final changes are documentation/evidence only.
