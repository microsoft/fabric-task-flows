---
id: skillset-selection
title: Skillset Selection (Code-First vs Low-Code)
description: Understand when to use Code-First [CF] vs Low-Code [LC] item types based on team skills and requirements
triggers:
  - "code first vs low code"
  - "CF vs LC"
  - "no code option"
  - "need python"
  - "business user"
  - "developer vs analyst"
options:
  - id: code-first
    label: Code-First [CF]
    criteria:
      skills: ["Python", "Spark", "SQL", "KQL", "Scala"]
      personas: ["Data Engineer", "Data Scientist", "ML Engineer"]
      flexibility: high
      learning_curve: steep
      best_for: ["complex transformations", "ML", "custom logic", "CI/CD"]
  - id: low-code
    label: Low-Code [LC]
    criteria:
      skills: ["Point-and-click", "Power Query", "drag-and-drop"]
      personas: ["Business Analyst", "Citizen Developer", "BI Developer"]
      flexibility: moderate
      learning_curve: gentle
      best_for: ["quick prototypes", "business-maintained ETL", "standard patterns"]
  - id: hybrid
    label: Hybrid [LC/CF]
    criteria:
      skills: ["Both approaches"]
      personas: ["Mixed teams"]
      flexibility: maximum
      best_for: ["enterprise deployments", "shared ownership", "progressive complexity"]
quick_decision: |
  Engineers + Python/Spark/SQL → Code-First [CF]
  Engineers + prefer visual tools → Low-Code [LC]
  Business Analysts + Power Query → Low-Code [LC]
  Mixed team (engineers + analysts) → Hybrid [LC/CF]
---

# Skillset Selection: Code-First vs Low-Code

> Understanding the [CF] and [LC] tags used throughout task flows to choose the right tools for your team's skills and requirements.

## Tag Reference

Throughout the task flow documentation, you'll see these tags:

| Tag | Meaning | Target Persona |
|-----|---------|----------------|
| **[LC]** | Low-Code | Business Analysts, Citizen Developers |
| **[CF]** | Code-First | Data Engineers, Data Scientists |
| **[LC/CF]** | Both Supported | Mixed Teams |

## Quick Decision Tree

```
Who will BUILD and MAINTAIN this solution?
│
├─► Data Engineers / Developers
│   │
│   └─► Comfortable with Python, Spark, SQL?
│       │
│       ├─► YES ──────────────────────────► Code-First [CF]
│       │
│       └─► NO, prefer visual tools ──────► Low-Code [LC]
│
├─► Business Analysts / Citizen Developers
│   │
│   └─► Do they know Power Query / Excel?
│       │
│       ├─► YES ──────────────────────────► Low-Code [LC]
│       │
│       └─► NO ───────────────────────────► Training needed
│
└─► Mixed Team (Engineers + Analysts)
    │
    └─► Use [LC/CF] items where possible ─► Hybrid approach
```

## Comparison Table

| Criteria | Code-First [CF] | Low-Code [LC] |
|----------|-----------------|---------------|
| **Primary Skills** | Python, Spark, SQL, KQL, Scala | Power Query, drag-and-drop, point-and-click |
| **Learning Curve** | Steep (weeks to months) | Gentle (days to weeks) |
| **Flexibility** | Maximum - any logic possible | Moderate - within tool capabilities |
| **Debugging** | Full programmatic debugging | Limited visual debugging |
| **Version Control** | ✅ Full Git integration | Limited or manual |
| **CI/CD** | ✅ Standard pipelines | Requires workarounds |
| **Reusability** | Functions, libraries, modules | Templates, copy/paste |
| **Scalability** | Excellent (Spark distributed) | Good for small-medium |
| **Collaboration** | Pull requests, code review | Workspace sharing |

## Item Types by Skillset

### Code-First [CF] Items

| Item Type | Primary Language | Use Case |
|-----------|-----------------|----------|
| **Notebook** | Python, Spark SQL, Scala, R | Interactive development, ML, transformations |
| **Spark Job Definition** | Python, Spark SQL | Scheduled production jobs |
| **Environment** | YAML/Python | Library management, Spark config |
| **KQL Queryset** | KQL | Time-series analysis, Eventhouse queries |
| **Experiment** | Python (MLflow) | ML model training and tracking |
| **ML Model** | Python | Model deployment and serving |
| **dbt Project** | SQL + YAML | SQL transformations with dbt |

### Low-Code [LC] Items

| Item Type | Interface | Use Case |
|-----------|-----------|----------|
| **Copy Job** | Visual wizard | Simple data movement |
| **Dataflow Gen2** | Power Query UI | Visual ETL transformations |
| **Lakehouse** | Point-and-click | Storage creation and management |
| **Warehouse** | Visual + T-SQL | DW tables and views |
| **Report** | Power BI Desktop/Web | Interactive visualizations |
| **Paginated Report** | Report Builder | Print-ready reports |
| **Scorecard** | Web UI | Goal tracking |
| **Eventstream** | Visual canvas | Stream routing |
| **Real-Time Dashboard** | Visual designer | Live monitoring |
| **Activator** | Rule builder | Trigger-based alerts |

### Hybrid [LC/CF] Items

| Item Type | Low-Code Option | Code-First Option |
|-----------|-----------------|-------------------|
| **Pipeline** | Visual activities | Expression language, parameters |
| **Semantic Model** | Power BI Desktop | TMDL, Tabular Editor |
| **Warehouse** | Visual query editor | T-SQL stored procedures |
| **Datamart** | Visual modeling | SQL views |

## Workforce Planning

### Code-First Team Requirements

| Role | Skills Needed | Items They'll Use |
|------|--------------|-------------------|
| **Data Engineer** | Python, Spark, SQL, Git | Notebook, Spark Job Def, Pipeline, Environment |
| **Data Scientist** | Python, ML frameworks, Statistics | Notebook, Experiment, ML Model |
| **Analytics Engineer** | SQL, dbt, YAML | dbt Project, Warehouse, Notebook |
| **Platform Engineer** | Python, Git, CI/CD | All [CF] items, deployment pipelines |

### Low-Code Team Requirements

| Role | Skills Needed | Items They'll Use |
|------|--------------|-------------------|
| **Business Analyst** | Power Query, Excel, Power BI | Dataflow Gen2, Report, Scorecard |
| **BI Developer** | Power BI, DAX, data modeling | Semantic Model, Report |
| **Citizen Developer** | Drag-and-drop, basic logic | Copy Job, Dataflow Gen2, Eventstream |
| **Operations Analyst** | Monitoring, dashboards | Real-Time Dashboard, Activator |

### Hybrid Team Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID TEAM STRUCTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DATA PLATFORM TEAM (Code-First)                               │
│  └─► Notebooks, Spark Jobs, Environments, Pipelines            │
│      └─► Build reusable patterns and foundations               │
│                                                                 │
│              ▼                                                  │
│                                                                 │
│  ANALYTICS TEAM (Low-Code)                                      │
│  └─► Reports, Dashboards, Scorecards, Dataflows                │
│      └─► Consume curated data, build visualizations            │
│                                                                 │
│              ▼                                                  │
│                                                                 │
│  BUSINESS USERS                                                 │
│  └─► View Reports, Track Scorecards, Receive Alerts            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Evolution Paths

### Low-Code to Code-First

When you outgrow Low-Code tools:

| From (LC) | To (CF) | When to Evolve |
|-----------|---------|-----------------|
| Dataflow Gen2 | Notebook | Complex logic, large scale, reusability |
| Copy Job | Pipeline + Notebook | Conditional logic, error handling |
| Visual Warehouse | Stored Procedures | Complex transformations |
| Report (manual refresh) | Report + Pipeline | Automated refresh orchestration |

### Code-First to Low-Code

When to simplify:

| From (CF) | To (LC) | When to Evolve |
|-----------|---------|-----------------|
| Simple Notebook | Dataflow Gen2 | Business user maintenance |
| Spark aggregations | Semantic Model measures | Standard BI calculations |
| Custom alerting code | Activator | Rules-based triggers |

## Decision Matrix by Use Case

| Use Case | Small Scale / Quick | Large Scale / Production |
|----------|---------------------|--------------------------|
| **Data Ingestion** | Copy Job [LC] | Pipeline + Notebook [CF/LC] |
| **Transformations** | Dataflow Gen2 [LC] | Notebook / Spark Job [CF] |
| **Data Quality** | Dataflow Gen2 rules [LC] | Notebook with Great Expectations [CF] |
| **ML Training** | AutoML (limited) [LC] | Notebook + MLflow [CF] |
| **Visualization** | Report [LC] | Report with TMDL [LC/CF] |
| **Alerting** | Activator [LC] | Custom code + Azure Functions [CF] |

## Common Patterns

### Pattern 1: Code-First Foundation, Low-Code Consumption

```
Notebook [CF] ──► Lakehouse [LC] ──► Semantic Model [LC/CF] ──► Report [LC]
     │                │
     │                └─► Warehouse [LC] ──► Paginated Report [LC]
     │
     └─► Quality assured, governed data for business consumption
```

### Pattern 2: Low-Code End-to-End

```
Copy Job [LC] ──► Dataflow Gen2 [LC] ──► Semantic Model [LC] ──► Report [LC]
     │
     └─► Fast time-to-value, business-maintained
```

### Pattern 3: Code-First End-to-End

```
Pipeline [LC/CF] ──► Notebook [CF] ──► Lakehouse ──► Notebook [CF] ──► Report [LC]
     │
     └─► Maximum flexibility, engineering-maintained
```

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Force business users to write Python | Skill gap, maintenance burden | Use Low-Code for their layer |
| Use Dataflow Gen2 for Spark-scale data | Performance limits | Use Notebook |
| Skip code review for notebooks | Quality, knowledge sharing | Implement Git + PR workflow |
| Duplicate logic in LC and CF | Maintenance nightmare | Choose one, expose results |

## Related Decisions

- [Storage Selection](storage-selection.md) - [LC] and [CF] storage options
- [Ingestion Selection](ingestion-selection.md) - [LC] and [CF] ingestion methods
- [Processing Selection](processing-selection.md) - [LC] and [CF] processing tools
- [Visualization Selection](visualization-selection.md) - Primarily [LC] with [CF] options
