# Complete multi-project delivery

Use when the user requests an entire challenge/repository outcome. Read its
actual brief before deciding acceptance; do not assume a fixed stack, endpoint
count, test count, file tree or dependency upgrade from another run.

## Before transformation

Identify all target projects and report destinations. Record original revision,
source inventory and package hash. Inspect each original against the catalog;
manual baseline findings and existing reports are comparison material, not a
substitute for direct source evidence. Keep earlier finished implementations out
of the transformation input and do not cherry-pick their application/test files.

Present each project's audit, contract inventory, intended differences, dependency
groups, migration/rollback and approval scope. Ask for explicit human approval
after presenting them. A request to restart or iterate is not a fabricated approval
record. Read-only stages do not write reports, install or boot applications.

If the task requires manual analysis before skill construction, preserve the real
chronology and distinguish later corrections. For subsequent executions, do not
pretend the first analysis or a previous human approval happened again.

## After approval: skill-owned execution

Save the presented audit with the actual approval and revision recheck before
source edits. Build baseline tests from original behavior, then generate and test
each approved transformation using the playbook. Own all subsequent fixes inside
the same recorded skill run, including those found by review and final validation.
Produce implementation and documentation from this execution, not an earlier
finished checkout. Each recorded step identifies input revision/package hash,
finding IDs, command/action, observed result and changed files.

Iterate while new evidence supports progress. If guidance proves insufficient,
update the reusable skill instruction, synchronize copies and rerun the affected
cases. When the instruction changes materially, repeat the relevant original-
project evaluation with the final package. Do not add a hidden human cleanup step.

## Deliverables and acceptance

For a refactoring challenge, generate within Phase 3:

- an initial audit per project, with counts calculated from ordered findings,
  exact original lines/revision, evidence, impacts and recommended verification;
- a validation report per project: baseline, changes mapped to findings, boot,
  all inventoried contracts, regression results, migration and unresolved items;
- sanitized execution logs and runnable validation commands using disposable data;
- README sections for manual findings, skill construction/design, measured
  results and how to execute. Include before/after structure, counts per severity,
  individual project checklists, logs and observations across stacks;
- local skill packages with relative references; compare full-file hashes across
  copies, not just SKILL.md, and document the version used in every run.

When the brief prescribes reports/audit-project-N.md, use those paths relative to
the repository root and a separate validation-project-N.md for later results.
Do not overwrite raw measurements to make them agree with a revised rubric;
record any correction and recompute the delivered summary separately.

Evaluate detection on the original, not only on already-correct code. Apply the
brief's finding minimums to its original targets, never force them onto a clean
control or re-audit. A structural checker is useful but cannot prove boot, HTTP
behavior, authorship or actual human approval.

Finally reproduce setup and validation in a clean checkout, confirm tracked
packages/reports/code, and exclude real secrets, environments, databases and caches.
If public GitHub delivery is required, verify visibility, fork parent, submitted
branch and remote content. Publish only within the user's authorization. If the
source changes after testing, rerun affected checks before declaring completion.
