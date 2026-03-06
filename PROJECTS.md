# Projects

> Status dashboard for all Fabric projects managed by this repository.

| Project | Task Flow | Phase | Status | Blockers | Next Action |
|---------|-----------|-------|--------|----------|-------------|
| [old-style](projects/old-style/) | basic-data-analytics | Design Review ✅ | Final | 5 critical, 2 medium | Resolve blockers → Deploy |
| [FraudDetection](projects/FraudDetection/) | lambda | Documented ✅ | Complete | 0 | — |

## Phase Legend

| Phase | Description |
|-------|-------------|
| Design | Architect producing DRAFT handoff |
| Design Review | Engineer + Tester reviewing DRAFT |
| Design Review ✅ | Architect incorporated feedback → FINAL handoff |
| Test Plan | Tester producing test plan from FINAL handoff |
| Deploying | Engineer deploying items by wave |
| Deployed | All items created; manual steps may remain |
| Validating | Tester running validation checklist |
| Validated ✅ | All checks passed |
| Documented ✅ | Documenter produced wiki + ADRs |
| Complete | All phases finished |

## How to Use

1. **Starting a new project?** Add a row with Phase = "Design" and invoke `@fabric-architect`
2. **Resuming work?** Check this table → read the project's `STATUS.md` for details → invoke the next agent
3. **Agents update this table** as part of their handoff output

See [`_shared/workflow-guide.md`](\_shared/workflow-guide.md) for step-by-step prompts for each phase transition.
