# Validation Checklist

Post-deployment validation for Event Analytics task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Eventhouse | Create KQL databases; configure retention policies |
| Eventstream | Configure source connections (Event Hubs, Kafka, etc.) |
| Copy job | Configure source/destination connections |
| Pipeline | Configure external connections; set triggers/schedule |
| Activator | Configure alert conditions and actions |
| KQL Queryset | Attach to Eventhouse database |
| Notebook | Attach to Eventhouse; configure Environment |
| Real-Time Dashboard | Bind to Eventhouse; configure auto-refresh |
| Report | Verify data source binding |

## Checklist

### Phase 1: Foundation

- [ ] Eventhouse created
- [ ] KQL database(s) provisioned
- [ ] Environment configured (if using notebooks)

### Phase 2: Real-Time Ingestion

- [ ] Eventstream created and connected to source
- [ ] Data flowing into Eventhouse
- [ ] Activator alerts configured (if using)
- [ ] Test alert triggered

### Phase 3: Batch Ingestion

- [ ] Copy job / Pipeline / Dataflow created
- [ ] Batch data loaded into Eventhouse
- [ ] Schedule configured

### Phase 4: Query & Analysis

- [ ] KQL Queryset connected to database
- [ ] Queries returning results
- [ ] Notebooks running (if using data science)
- [ ] ML experiment tracking (if applicable)

### Phase 5: Visualization

- [ ] Real-Time Dashboard rendering live data
- [ ] Report created with correct data bindings
- [ ] Dashboard combining views (if using)
