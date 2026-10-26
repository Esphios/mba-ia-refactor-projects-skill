# Evidence catalog

Severity is contextual. Confirm reachability, trust boundary and impact; record a
suspicion when evidence is incomplete. A keyword or folder name is never sufficient.
When an explicit assessment rubric exists, follow it and explain any proposed
exception. Exposed passwords/hashes and operational hardcoded credentials are
CRITICAL under a sensitive-data rubric even when weak storage is also present.
Examples/placeholders with no access are not evidence of a live compromised secret.

| ID / family | Typical severity | Confirming signals | False-positive check |
| --- | --- | --- | --- |
| AP-01 SQL injection | CRITICAL | untrusted domain input changes SQL syntax | placeholders are safe; an explicitly approved, authenticated admin SQL console is a privileged tool, not a domain-input false positive |
| AP-02 hardcoded/exposed secrets | CRITICAL | usable credential in code, response or log | placeholder/example with no access is not a secret |
| AP-03 God Class/multiple domains | CRITICAL | one unit owns unrelated routes, schema, rules and integrations | size alone is insufficient |
| AP-04 insecure passwords/tokens | HIGH | plaintext/fast hash, unverifiable or non-expiring token | cryptographic hash is not automatically a password hash |
| AP-05 missing authorization | HIGH | sensitive action lacks identity/role/ownership check | authentication performed by verified upstream middleware may apply |
| AP-06 global/shared connection | HIGH | unsafe shared mutable lifecycle across requests | managed pool or scoped session is not equivalent |
| AP-07 partial writes | HIGH | multi-entity operation commits in pieces or lacks rollback | one atomic statement may need no explicit transaction |
| AP-08 N+1 queries | MEDIUM | query inside a result loop grows with rows | bounded lookup or eager-loaded relationship may be acceptable |
| AP-09 duplicated validation/serialization | MEDIUM | copies diverge or encode the same rule repeatedly | similar code with different domain policy is not duplication |
| AP-10 deprecated API | MEDIUM | applicable installed/declared version and official source mark it deprecated | old-looking API without version/source remains unverified |
| AP-11 magic values | LOW | unexplained repeated domain thresholds/statuses | protocol constants and obvious local literals may be clear |
| AP-12 opaque names/dead code | LOW | misleading identifiers or proven unused imports/exports | public request keys may be contractual and must remain |

## Deprecation evidence

Record dependency/runtime version, official source URL, deprecation statement,
replacement and compatibility impact. Examples that require version confirmation:
SQLAlchemy 2.x documents `Query.get()` as legacy in favor of `Session.get()`;
Python 3.12 deprecates `datetime.utcnow()` in favor of explicit UTC-aware time.
Do not label either finding confirmed until the applicable runtime is established.
