---
name: refactor-arch
description: Use when analyzing or refactoring a legacy application toward MVC while preserving HTTP behavior, auditing architecture and security findings, and requiring explicit approval before changes.
---

# Refactor Architecture

Analyze evidence first, obtain informed approval, then refactor incrementally. The
project under the current working directory is the default input; accept a different
project path and report destination when the user supplies them.

For a multi-project challenge or complete repository delivery, read
[delivery.md](references/delivery.md). This workflow owns implementation, tests,
regression fixes, reports and documentation; do not leave unrecorded final fixes
to an executor outside the skill.

## Invariants

- Phases 1 and 2 are read-only: do not install, start servers, create databases,
  run seeds, or write reports.
- Show the audit, plan, dependencies, and every intended contract difference in
  the conversation. Then stop. Silence and earlier generic requests are not approval.
- Phase 3 starts only after a human explicitly approves that presented result.
- At continuation, verify the revision and working-tree state. Re-audit changed
  evidence and reconfirm material differences.
- Modify only approved findings. If a selected correction depends on an unselected
  change, explain the dependency and wait for scope expansion.
- Preserve legitimate methods, paths, inputs, status codes, response shapes, and
  business effects. Security changes are contract differences, not permission to
  disable a functional route.
- An explicitly approved administrative SQL console may retain arbitrary SQL when
  protected by verified administrator access and documented as an exceptional trust
  boundary. Do not silently convert it to read-only, allowlist it, or remove it.
- Never run a destructive seed or operate on an existing database without a backup
  and explicit test/migration plan. Prefer disposable databases.

## Phase 1 — Project analysis

Read [project-analysis.md](references/project-analysis.md) and inspect repository
instructions before analyzing. Report language/framework, declared and verified
versions separately, dependencies, persistence, domain, current architecture,
entry points, method/path inventory, source-file count, exclusions, revision, and
working-tree state. Label uncertainty as unverified. If the stack cannot be safely
identified, state what evidence is missing and stop instead of applying a familiar
template.

## Phase 2 — Audit and approval gate

Read [anti-patterns.md](references/anti-patterns.md) and
[audit-report-template.md](references/audit-report-template.md). Findings require
direct evidence and are ordered CRITICAL to LOW. Do not manufacture a minimum count;
an already-correct project may have no findings.

Apply the user's severity rubric when supplied. Password/hash disclosure and
operational credentials embedded in source belong to exposed-sensitive-data
findings, not just weak-hash findings. Recalculate summaries from the findings.

Read [mvc-guidelines.md](references/mvc-guidelines.md) to propose an architecture
that retains explicit Models, Views/Routes, and Controllers. Add services only for
meaningful orchestration, transactions, or integrations. Read
[refactoring-playbook.md](references/refactoring-playbook.md) only for transformations
corresponding to confirmed findings.

Present:

1. revision and analysis scope;
2. severity summary and complete findings;
3. proposed transformations and dependencies;
4. method/path contract inventory;
5. intentional contract differences, migration and rollback impacts;
6. selectable scope by finding or severity;
7. the exact report path that will be written after approval.

Ask for explicit approval of this result and stop without writing. A refusal ends
the run unchanged. Partial approval remains partial and does not imply acceptance
of dependent findings.

## Phase 3 — Approved transformation

After approval, first verify the audited revision and save the approved audit. Read
[validation.md](references/validation.md). Establish a characterization baseline in
an isolated environment, then change one coherent slice at a time:

1. write or extend a failing test for the approved behavior;
2. make the smallest architectural or security change;
3. run the focused test and relevant regression suite;
4. record finding-to-change and contract evidence.

Validate real boot plus every inventoried method/path using disposable data. Test
authorized success as well as denial; 401/403 alone never proves a protected feature
still works. Re-audit after tests pass and report unresolved findings honestly.
Read [regression-checks.md](references/regression-checks.md) when designing the
baseline and again before final acceptance. Every defect discovered by review or
validation remains inside this workflow: add evidence, reproduce with a test,
correct it, rerun affected checks and update the audit-to-change mapping.

An earlier refactored checkout is not an implementation input. Generate changes
from the inspected original, approved findings and these references; never restore
finished application files, tests or reports from a prior solution to simulate a run.

## Failure and correction limit

A corrective cycle is diagnosis, a reproducible failure, one evidence-based change
and rerunning affected validation. Distinct, productive corrections are not three
attempts at the same failure. Stop an unchanged failure after three unsuccessful
attempts, or sooner without a new supported hypothesis. When the user requests
continued iteration, continue independent fixes and new evidence-based hypotheses;
pause only for missing authorization, required external input or lack of progress.
Preserve logs and pending criteria. Never weaken acceptance checks to end a loop.

## Common mistakes

| Mistake | Required response |
| --- | --- |
| Folder names look like MVC | Trace responsibilities and dependencies; names are not evidence. |
| A security fix changes behavior | List it as a contract difference and obtain approval. |
| A selected finding needs another fix | Pause and request the dependent scope explicitly. |
| A route is risky | Preserve an authorized functional flow unless removal was specifically approved. |
| An admin SQL console accepts SQL text | Treat authorization as the boundary when its arbitrary-SQL function is approved. |
| Validation is static only | Run real boot and HTTP contracts in Phase 3. |
| Same failure persists without progress | Stop that attempt with diagnosis; never claim success or weaken tests. |
