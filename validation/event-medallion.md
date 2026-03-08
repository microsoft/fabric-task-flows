# Validation Checklist

Post-deployment validation for Event Medallion task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Eventhouse | Verify permissions; configure KQL databases |
| Eventstream | Configure event source; start stream |
| Copy Job | Configure source connections (batch) |
| Pipeline | Configure activities and schedule |
| KQL Queryset | Configure materialized views; update policies |
| Real-Time Dashboard | Configure tiles; set refresh |
| Report | Verify data source binding |
| Activator | Configure trigger conditions; set actions |

## Checklist

### Phase 1: Foundation

- [ ] Eventhouse created
- [ ] KQL Database (Bronze) created
- [ ] KQL Database (Silver) created
- [ ] KQL Database (Gold) created

### Phase 2: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 3: Ingestion

- [ ] Real-time ingestion configured:
  - [ ] Eventstream connected to source
  - [ ] Eventstream routing to Bronze
- [ ] Batch ingestion configured (if applicable):
  - [ ] Copy Job or Pipeline configured
  - [ ] Data loading to Bronze

### Phase 4: Transformation

- [ ] KQL Queryset created
- [ ] Bronze → Silver transformation working
- [ ] Silver → Gold aggregations working
- [ ] Update policies configured (continuous ingestion)
- [ ] Materialized views created

### Phase 5: Visualization

- [ ] Real-Time Dashboard created
- [ ] Dashboard tiles connected to Gold
- [ ] Report created (for historical analysis)
- [ ] Refresh configured

### Phase 6: Monitoring

- [ ] Activator configured (if applicable)
- [ ] Alert conditions defined
- [ ] Actions configured (email, Teams, etc.)
