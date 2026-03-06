# Status: old-style

> Detailed progress tracker for the old-style Oracle migration project.

## Current State

| Field | Value |
|-------|-------|
| **Task Flow** | basic-data-analytics |
| **Phase** | Design Review Complete |
| **Status** | Final — ready for deployment (pending blocker resolution) |
| **Next Phase** | Deployment |

---

## Phase Progression

| Phase | Agent | Date | Notes |
|-------|-------|------|-------|
| Design | @fabric-architect | 2025-07-16 | DRAFT handoff produced. Oracle → Warehouse migration, T-SQL team, batch only. |
| Design Review | @fabric-engineer | 2026-03-06 | 9 findings: 2 🔴 (wave order, missing DDL wave), 7 🟡/🟢. All resolved. |
| Design Review | @fabric-tester | 2026-03-06 | 11 findings: 3 🔴 (untestable ACs, missing Direct Lake AC, B-5 severity), 8 🟡. All resolved. |
| Design Review ✅ | @fabric-architect | 2026-03-06 | Incorporated all feedback. 5 waves (was 3), AC-8 added, ACs tightened, B-5 elevated. |
| Test Plan | @fabric-tester | 2025-07-16 | 8 ACs, 29 checks, 11 edge cases, 7 blockers. Updated post-Design Review. |
| Deployment | — | — | ⏳ Blocked — 5 critical blockers unresolved |
| Validation | — | — | ⏳ Waiting for deployment |
| Documentation | — | — | ⏳ Waiting for validation |

---

## Blockers

| # | Description | Severity | Raised | Resolved | Notes |
|---|-------------|----------|--------|----------|-------|
| B-1 | Oracle connection details (host, port, SID, schema, credentials, gateway?) | 🔴 Critical | 2025-07-16 | ❌ | Team must provide |
| B-2 | DDL scripts for Warehouse objects (tables, stored procs, views) | 🔴 Critical | 2025-07-16 | ❌ | Store in `projects/old-style/sql/` |
| B-3 | Oracle baseline query times for performance comparison | 🟡 Medium | 2025-07-16 | ❌ | If unavailable, Warehouse times become baseline |
| B-4 | Fabric capacity assignment to workspace | 🔴 Critical | 2025-07-16 | ❌ | F2/F4 sufficient for dev |
| B-5 | Semantic Model design (tables, relationships, DAX measures) | 🔴 Critical | 2025-07-16 | ❌ | Elevated from 🟡 during Design Review |
| B-6 | Oracle table/schema inventory | 🔴 Critical | 2026-03-06 | ❌ | Added during Design Review |
| B-7 | Data volume estimates | 🟡 Medium | 2026-03-06 | ❌ | Affects partitioning and capacity sizing |

---

## Deployment Wave Progress

| Wave | Items | Status | Notes |
|------|-------|--------|-------|
| 1 | Warehouse (shell) | ⏳ Not started | `fab mkdir` |
| 2 | DDL deployment | ⏳ Not started | DACPAC or sqlcmd — requires B-2 |
| 3 | Pipeline | ⏳ Not started | Requires B-1 (Oracle connection) |
| 4 | Semantic Model | ⏳ Not started | Requires B-5 (design), manual connection config |
| 5 | Report | ⏳ Not started | Requires Semantic Model |

---

## Manual Steps

| # | Step | Status | Notes |
|---|------|--------|-------|
| M-1 | Create Oracle source connection | ⬜ | Requires B-1 |
| M-2 | Install on-prem data gateway (if Oracle is on-prem) | ⬜ | Confirm Oracle location first |
| M-3 | Deploy DDL to Warehouse | ⬜ | Requires B-2 |
| M-4 | Configure Semantic Model data source credentials | ⬜ | First deployment requires manual config |
| M-5 | Verify Report ↔ Semantic Model binding | ⬜ | After Wave 5 |
| M-6 | Set Pipeline schedule/trigger | ⬜ | Clarify: one-time migration or ongoing sync? |

---

## Key Documents

| Document | Path |
|----------|------|
| Architecture Handoff | [`projects/old-style/deployments/handoff.md`](deployments/handoff.md) |
| Test Plan | [`projects/old-style/docs/test-plan.md`](docs/test-plan.md) |
| Diagram | [`diagrams/basic-data-analytics.md`](../../diagrams/basic-data-analytics.md) |
| Validation Checklist | [`validation/basic-data-analytics.md`](../../validation/basic-data-analytics.md) |
