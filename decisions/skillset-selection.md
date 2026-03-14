---
id: skillset-selection
title: Skillset Selection (Code-First vs Low-Code)
---

# Skillset Selection: Code-First vs Low-Code

## Tag Reference

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

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Force business users to write Python | Skill gap, maintenance burden | Use Low-Code for their layer |
| Use Dataflow Gen2 for Spark-scale data | Performance limits | Use Notebook |
| Skip code review for notebooks | Quality, knowledge sharing | Implement Git + PR workflow |
| Duplicate logic in LC and CF | Maintenance nightmare | Choose one, expose results |

## Related Decisions

- [Storage Selection](storage-selection.md)
- [Ingestion Selection](ingestion-selection.md)
- [Processing Selection](processing-selection.md)
- [Visualization Selection](visualization-selection.md)
