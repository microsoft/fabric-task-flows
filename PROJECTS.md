# Projects

> Status dashboard for all Fabric projects managed by this repository.

| Project | Task Flow | Phase | Status | Blockers | Next Action |
|---------|-----------|-------|--------|----------|-------------|
| chicago-bears-85 | medallion | Test Plan ✅ | Test plan produced (15 ACs, 5 blockers) | Capacity, gateway, Oracle connection, table list, test user | User Sign-Off (Phase 2b) |
| grid-operations-intelligence | lambda | Design Review ✅ | FINAL handoff produced (17 items, reviews incorporated) | F64 capacity | Test Plan (Phase 2a) |
| energy-field-intelligence | TBD | Discovery | Discovery Brief produced | None | Architecture Design (Phase 1a) |

| power-up-intelligence | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| financial-analytics-platform | TBD | Discovery ✅ | Discovery Brief produced | None | Architecture Design (Phase 1a) |
| contoso-sales-modernization | medallion | Validated ✅ | Partial — structural verified, data-flow deferred (design-only) | D-1 table list, D-2 credentials, D-3 data volume | Documentation (Phase 4) |
| energy-advisor | lambda | Documented ✅ | Pipeline complete — 15 items, 5 ADRs, partial validation (B-1 pending) | B-1 meter source, B-2 capacity SKU | Resolve blockers → full validation |
| energy-advisor-v2 | lambda | Documented | 15 items, 5 waves, 18 ACs — pipeline complete | B-1, B-2, B-4 | Deploy to workspace |
| customer-360 | medallion (composite) | Test Plan ✅ | FINAL handoff + test plan produced (20 items, 21 ACs) | B-1 data sources, B-2 regulations, B-3 capacity, B-4 flag definition | User Sign-Off (Phase 2b) |
| energy-ops-proactive | lambda | Test Plan ✅ | FINAL handoff + test plan produced (15 items, 23 ACs, 5 waves) | B-1 IoT source, B-2 DB type, B-3 capacity, B-6 thresholds, B-7 ML baseline | User Sign-Off (Phase 2b) |
| contoso-sales | TBD | Discovery ✅ | Discovery Brief produced | None | Architecture Design (Phase 1a) |
| media-server | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| project-bluefish | medallion | Design | DRAFT handoff produced (9 items, 14 ACs, 7 waves) | B-1 source DBs, B-2 file formats, B-3 SSIS inventory, B-4 capacity | Design Review (Phase 1b) |
| contoso-call-intelligence | TBD | Discovery ✅ | Discovery Brief produced | None | Architecture Design (Phase 1a) |
| call-center-ai | lambda | Design | DRAFT handoff produced (15 items, 7 waves, 18 ACs) | B-1 telephony vendor, B-2 volume, B-3 capacity | Design Review (Phase 1b) |
| contoso-insights | medallion | Deployed | Scripts generated (.sh + .ps1); blockers prevent live deploy | B-1 SQL conn, B-2 tables, B-3 capacity | Resolve blockers → run scripts → Validate |
| application-insights-finder | medallion | Deployed | Scripts generated (.sh + .ps1); design-only mode | B-1 SQL conn, B-2 tables, B-3 capacity | Resolve blockers → run scripts → Validate |
| agent-assist-telco | lambda | Documented ✅ | Pipeline complete — 15 items, 5 ADRs, partial validation | B-1 telephony, B-2 Dataverse, B-3 capacity | Resolve blockers → deploy |
| real-time-trigger-factory | event-analytics | Documented ✅ | Pipeline complete — 13 items, 5 ADRs, partial validation (design-only) | B-1 Event Hub, B-2 capacity | Resolve blockers → deploy |

| energy-saver-pro | lambda | Test Plan ✅ | FINAL handoff + test plan (15 items, 6 waves, 21 ACs) | B-1 SCADA, B-2 DB engine, B-3 capacity, B-4 thresholds | User Sign-Off (Phase 2b) |
| social-pulse | lambda | Documented ✅ | Pipeline complete — 15 items, 5 ADRs, partial validation (3 portal-only pending) | D-1 Event Hub, D-2 API credentials | Resolve external prerequisites → portal items |

| football-intelligence | medallion | Test Plan ✅ | FINAL handoff + test plan produced; 2 revision cycles used | None | User Sign-Off (Phase 2b) |
| football-intelligence-v2 | medallion | Test Plan ✅ | FINAL handoff + test plan produced | None | User Sign-Off (Phase 2b) |
| campaign-command | lambda | Documented ✅ | Pipeline complete — all phases finished | None | Complete |
| retail-of-the-future | medallion | Deploying | Approved; deployment in progress | None | Validate (Phase 3) |
| utility-meter-modernization | lambda | Documented ✅ | Pipeline complete — 14 items, 5 ADRs, partial validation (8 manual steps pending) | D-1 Event Hub, D-2 source DB creds | Resolve external prerequisites → complete manual steps |
| modern-dw-stuff | medallion | Test Plan ✅ | FINAL handoff + test plan produced | None | User Sign-Off (Phase 2b) |
| grid-intelligence | TBD | Design | Discovery Brief produced; DRAFT architecture in progress | None | Design Review (Phase 1b) |
| game-day-intelligence | medallion | Documented ✅ | Pipeline complete — 12 items, 5 ADRs, validation passed (1 ML Model manual) | None | Complete |
| game-day-intelligence-v2 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| gov-modernizer | medallion | Documented ✅ | Pipeline complete — 10 items, 5 ADRs, validation passed | D-1 SQL conn, D-2 capacity | Run deploy script → configure connections |
| tool-intelligence | medallion | Documented ✅ | Pipeline complete — 11 items, 6 ADRs, validation passed (design-only) | D-1 SQL conn, D-2 flat file path, D-3 capacity | Run deploy script → configure connections |
> Project rows are generated locally by agents. See `projects/` folder (gitignored) for per-project artifacts.

---

### Fleet Test Projects

> Auto-generated by `fleet-runner.py` for stress testing. These are not real projects.

<details>
<summary>20 fleet test projects (click to expand)</summary>

| Project | Task Flow | Phase | Status | Blockers | Next Action |
|---------|-----------|-------|--------|----------|-------------|
| fleet-batch-warehouse-1 | TBD | Discovery ✅ | Fleet run — candidates: basic-data-analytics, medallion | None | Architecture Design (Phase 1a) |
| fleet-batch-warehouse-2 | TBD | Discovery ✅ | Fleet run — candidates: basic-data-analytics, medallion | None | Architecture Design (Phase 1a) |
| fleet-batch-warehouse-3 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-batch-warehouse-4 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-batch-warehouse-5 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-real-time-streaming-6 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-real-time-streaming-7 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-real-time-streaming-8 | TBD | Discovery ✅ | Fleet run — candidates: event-analytics, event-medallion | None | Architecture Design (Phase 1a) |
| fleet-real-time-streaming-9 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-real-time-streaming-10 | TBD | Discovery ✅ | Fleet run — candidates: event-analytics, event-medallion | None | Architecture Design (Phase 1a) |
| fleet-hybrid-batch-real-time-11 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-hybrid-batch-real-time-12 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-hybrid-batch-real-time-13 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-analytics-ml-14 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-analytics-ml-15 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-analytics-ml-16 | TBD | Discovery ✅ | Fleet run — candidates: basic-machine-learning-models | None | Architecture Design (Phase 1a) |
| fleet-governance-security-17 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-governance-security-18 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-governance-security-19 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |
| fleet-vague-ambiguous-maximum-stress-test-20 | TBD | Discovery | Scaffolded — awaiting Discovery Brief | None | Discovery (Phase 0a) |

</details>

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
