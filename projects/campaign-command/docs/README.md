# Campaign Command — Architecture Documentation

> Generated: 2026-03-09
> Task flow: lambda + conversational-analytics (overlay)
> Status: VALIDATED

## Overview

Campaign Command is a Lambda architecture for a marketing company, combining batch analytics (Google Analytics, AdWords) with real-time social media sentiment monitoring. It includes an exec-facing Data Agent chatbot for self-service campaign performance Q&A.

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System diagram and item relationships |
| [Deployment Log](deployment-log.md) | What was deployed and how |
| [Deployments](../deployments/) | Scripts, notebooks, and queries |

### Decision Records

| ADR | Decision | Outcome |
|-----|----------|---------|
| [001-task-flow](decisions/001-task-flow.md) | Which task flow pattern? | Lambda + conversational-analytics overlay |
| [002-storage](decisions/002-storage.md) | Storage layer | Lakehouse + Warehouse + Eventhouse |
| [003-ingestion](decisions/003-ingestion.md) | Ingestion approach | Pipeline (batch) + Eventstream (real-time) |
| [004-processing](decisions/004-processing.md) | Processing/transformation | Notebook (Spark) + KQL Queryset |
| [005-visualization](decisions/005-visualization.md) | Visualization | Report + RT Dashboard + Data Agent |
