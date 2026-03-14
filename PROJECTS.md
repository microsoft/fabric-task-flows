# Projects

> Status dashboard for all Fabric projects managed by this repository.

| Project | Task Flow | Phase | Status | Blockers | Next Action |
|---------|-----------|-------|--------|----------|-------------|
| tractor-watch | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| shop-floor-analytics | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| smart-factory-hub | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| agops | event-medallion | Documented ✅ | 15 items deployed, 5 manual steps pending | None | Operational handoff |
| match-day-pulse | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
> Project rows are generated locally by agents. See `_projects/` folder (gitignored) for per-project artifacts.

## Phase Legend

| Phase | Description |
|-------|-------------|
| Discovery | Advisor producing Discovery Brief |
| Design | Architect producing DRAFT handoff |
| Design Review | Engineer + Tester reviewing DRAFT |
| Design Review ✅ | Architect incorporated feedback → FINAL handoff |
| Test Plan | Tester producing test plan from FINAL handoff |
| Approved ✅ | User reviewed architecture + test plan and approved deployment |
| Deploying | Engineer deploying items by wave |
| Deployed | All items created; manual steps may remain |
| Validating | Tester running validation checklist |
| Validated ✅ | All checks passed |
| Documented ✅ | Documenter produced wiki + ADRs |
| Complete | All phases finished |

## How to Use

1. **Starting a new project?** Add a row with Phase = "Discovery" and invoke `@fabric-advisor`
2. **Resuming work?** Check this table → read the project's `STATUS.md` for details → invoke the next agent
3. **Agents update this table** as part of their handoff output

See [`_shared/workflow-guide.md`](_shared/workflow-guide.md) for step-by-step prompts for each phase transition.
.
