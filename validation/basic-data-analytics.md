# Validation Checklist

Post-deployment validation for Basic Data Analytics task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Copy Job | Configure source/destination connections in UI |
| Dataflow Gen2 | Publish dataflow; set up refresh credentials |
| Pipeline | Configure external connections; set triggers |
| Semantic Model | Bind to Warehouse (if Direct Lake); set refresh credentials |
| Report | Verify semantic model binding |
| Activator | Configure alert conditions and actions |

## Checklist

### Phase 1: Warehouse

- [ ] Warehouse created and accessible
- [ ] Permissions configured

### Phase 2: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 3: Ingestion

- [ ] Ingestion item created (Copy Job / Dataflow / Pipeline)
- [ ] Connections configured
- [ ] Test run successful
- [ ] Data visible in Warehouse

### Phase 4: Semantic Layer

- [ ] Semantic Model created
- [ ] Bound to Warehouse
- [ ] Measures and relationships validated
- [ ] Report created
- [ ] Visuals rendering correctly

### Phase 5: Monitoring

- [ ] Scorecard created (if using)
- [ ] Activator alerts configured (if using)
- [ ] Test alerts triggered successfully
