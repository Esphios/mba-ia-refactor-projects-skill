The `refactor-arch` skill is available in the discovered skills.

Resolved path: [SKILL.md](D:/Docs/Workspace/mba-ia-workspace/desafios/refactor-projects-skill/code-smells-project/.agents/skills/refactor-arch/SKILL.md)

Its three phases are:

1. **Project analysis** — Read-only inspection and reporting of the project’s stack, architecture, entry points, HTTP contracts, revision, and working-tree state.
2. **Audit and approval gate** — Present evidence-backed findings, proposed transformations, dependencies, contract differences, rollback impacts, and selectable scope.
3. **Approved transformation** — After approval, save the audit, establish characterization tests, implement approved changes incrementally, and validate the application and HTTP contracts.

Approval gate: Phase 3 may begin only after a human explicitly approves the complete Phase 2 result. Silence or a prior generic request does not count. Partial approval authorizes only the selected findings and does not implicitly approve dependencies.

No source audit, writes, installations, processes, or Git-changing commands were performed.