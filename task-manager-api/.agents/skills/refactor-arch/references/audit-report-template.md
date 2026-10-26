# Audit report contract

The Phase 2 conversation and the persisted post-approval report use this structure.

## Header

- project, revision, working-tree state and skill hash/version;
- analysis date, source count/exclusions and version confidence;
- method/path count and report destination.

## Summary

Count confirmed findings by CRITICAL, HIGH, MEDIUM and LOW. List suspicions
separately; they do not count as confirmed.

## Finding (repeat, ordered by severity)

- ID and anti-pattern catalog ID;
- confirmed/suspected and severity justification;
- relative file plus start/end lines;
- concise evidence and reachable scenario;
- impact;
- recommended transformation and verification;
- dependencies on other findings;
- expected contract effect (`preserved` or explicit difference).

## Plan and approval surface

- ordered transformations and rollback points;
- complete contract-difference table: method/path, before, after, reason, tests;
- data migration/retention decisions;
- selectable finding/severity scope and dependency groups;
- unresolved decisions and exact approval question.

After approval, append the human response, timestamp/revision check and approved
scope before any source edit. Never persist the report before approval during a
skill execution.
