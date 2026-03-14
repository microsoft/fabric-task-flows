# Phase 2b: User Sign-Off Guide

> **This is the only step where you — not an agent — make the final call.** Everything before this point is preparation. Everything after it creates real Fabric items in your workspace.

## Why This Matters

The agents have done the analysis: the architect designed the architecture with input from the engineer and tester, and the tester produced a test plan with acceptance criteria. But before anything is deployed, you should review both documents to make sure they match your expectations.

This is your chance to catch misunderstandings, adjust scope, or ask questions — **before** resources are created.

## What You're Reviewing

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│   FINAL Architecture Handoff    │     │          Test Plan              │
│                                 │     │                                 │
│  • Architecture diagram         │     │  • Acceptance criteria mapped   │
│  • Task flow selected           │     │  • Critical verification points │
│  • Decisions + rationale        │     │  • Edge cases identified        │
│  • Items to deploy              │     │  • Pre-deployment blockers      │
│  • Deployment order             │     │                                 │
│  • Alternatives considered      │     │                                 │
│                                 │     │                                 │
│  _projects/[name]/docs/            │     │  _projects/[name]/docs/            │
│  architecture-handoff.md        │     │  test-plan.md                   │
└─────────────────────────────────┘     └─────────────────────────────────┘
                         │                         │
                         └────────┬────────────────┘
                                  ▼
                        ✅ Your Approval
                                  │
                                  ▼
                         Phase 2c: Deploy
```

## Review Checklist

Walk through these before giving the go-ahead:

- **Review the auto-generated architecture diagram** — The pipeline runner automatically generates a validated ASCII diagram from the handoff's items/waves YAML via `.github/skills/fabric-design/scripts/diagram-gen.py`. This diagram is included in the sign-off prompt. It uses proper box-drawing characters with validated borders (no broken boxes). The diagram groups items by deployment wave so you can see what gets created in what order.
- **Does the architecture diagram clearly show how data flows from your sources to your outputs?** — The diagram should use your actual item names and make the end-to-end pipeline easy to follow
- **Does the task flow match your problem?** — Re-read the problem statement and make sure the selected pattern still feels right
- **Are the items what you expected?** — Check the deployment list for anything surprising or missing
- **Do the decisions make sense for your team?** — Storage, ingestion, processing, and visualization choices should align with your team's skills and preferences
- **Are acceptance criteria clear enough?** — You'll validate against these after deployment, so make sure they describe success in terms you understand
- **Any blockers to resolve first?** — The test plan may flag pre-deployment blockers (credentials, data sources, capacity) that need your action

## When You're Ready

- **Approve:** Say "approved" or "go ahead and deploy" to continue the pipeline.
  ```bash
  python _shared/scripts/run-pipeline.py advance --project my-project --approve
  ```

- **Request revisions:** If something doesn't look right, say "revise" with your feedback. The pipeline loops back to the architect (Phase 1c) to incorporate your changes, then regenerates the test plan and returns to sign-off.
  ```bash
  python _shared/scripts/run-pipeline.py advance --project my-project --revise --feedback "Change storage from Lakehouse to Warehouse for the Silver layer"
  ```

  The revision loop runs a maximum of **3 cycles**. After 3 revisions, you must either approve or reset the pipeline.

```
                         ✅ Your Approval ──────► Phase 2c: Deploy
                                │
                          ── OR ──
                                │
                         🔄 Request Revisions (max 3 cycles)
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Phase 1c: Finalize   │◄── Your feedback saved to
                    │  (Architect revises)  │    docs/sign-off-feedback.md
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Phase 2a: Test Plan  │
                    │  (Tester regenerates) │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Phase 2b: Sign-Off   │──► Review again
                    │  (You re-review)      │
                    └───────────────────────┘
```
