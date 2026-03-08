# Validation Checklist

Post-deployment validation for Lambda task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse | Verify permissions |
| Warehouse | Verify permissions; run initial DDL |
| Eventhouse | Configure retention policies |
| Environment | Configure Spark settings; publish |
| Copy Job | Configure batch source connections |
| Eventstream | Configure real-time source (Event Hub, etc.) |
| Notebook | Set default lakehouse |
| KQL Queryset | Deploy materialized views |
| Semantic Model | Bind to Warehouse; configure Direct Lake (recommended) or Import/DirectQuery |
| Real-Time Dashboard | Build dashboard tiles |
| Activator | Configure alert rules |

## Checklist

### Phase 1: Foundation

- [ ] Lakehouse(s) created (batch layer)
- [ ] Warehouse created (gold layer)
- [ ] Eventhouse created (speed layer)

### Phase 2: Environment

- [ ] Environment created and published

### Phase 3: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 4: Ingestion

- [ ] Batch ingestion working (Copy Job / Pipeline)
- [ ] Real-time ingestion working (Eventstream)

### Phase 5: Transformation

- [ ] Batch notebooks running
- [ ] KQL queries processing stream data

### Phase 6: Serving Layer

- [ ] Semantic Model bound to batch data
- [ ] Reports rendering batch views
- [ ] Real-Time Dashboard showing live data

### Phase 7: Monitoring & ML

- [ ] Activator configured for both layers
- [ ] ML models registered and scoring

### AI & Governance (Optional)

- [ ] Data Agent created (if using)
- [ ] Data Agent bound to appropriate data source (Lakehouse, Warehouse, KQL Database, or Semantic Model)
- [ ] Data Agent greeting and instructions configured
- [ ] Data Agent access permissions set
- [ ] Natural language query returns correct data (test 3-5 representative questions)
- [ ] Agent handles out-of-scope questions gracefully
- [ ] Ontology created (if using) with business terms mapped to data fields
