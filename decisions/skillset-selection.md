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

## Decision Matrix by Use Case

| Use Case | Small Scale / Quick | Large Scale / Production |
|----------|---------------------|--------------------------|
| **Data Ingestion** | Copy Job [LC] | Pipeline + Notebook [CF/LC] |
| **Transformations** | Dataflow Gen2 [LC] | Notebook / Spark Job [CF] |
| **Data Quality** | Dataflow Gen2 rules [LC] | Notebook with Great Expectations [CF] |
| **ML Training** | AutoML (limited) [LC] | Notebook + MLflow [CF] |
| **Visualization** | Report [LC] | Report with TMDL [LC/CF] |
| **Alerting** | Activator [LC] | Custom code + Azure Functions [CF] |

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
