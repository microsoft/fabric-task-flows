# Validation Checklist

Post-deployment validation for Medallion task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse (Bronze/Silver) | Verify permissions per layer |
| Gold Layer (Lakehouse OR Warehouse) | Verify permissions; configure based on chosen type |
| Environment | Configure Spark settings; publish environment |
| Copy Job | Configure source connections |
| Eventstream | Configure event source; start stream |
| Notebook | Set default lakehouse; verify environment attachment |
| Spark Job Def | Set default lakehouse; configure schedule |
| Semantic Model | Bind to Gold layer (Lakehouse or Warehouse); configure Direct Lake (recommended) or Import/DirectQuery |
| Report | Verify semantic model binding |

## Checklist

### Phase 1: Foundation

- [ ] Bronze Lakehouse created
- [ ] Silver Lakehouse created
- [ ] Gold layer created (choose ONE):
  - [ ] OPTION A: Lakehouse Gold (for Spark, ML, Delta Lake, read-only via SQL)
  - [ ] OPTION B: Warehouse Gold (for T-SQL read/write, BI, stored procedures)

### Phase 2: Environment

- [ ] Environment created and published
- [ ] Libraries installed

### Phase 3: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 4: Ingestion

- [ ] Ingestion items configured
- [ ] Data flowing to Bronze layer

### Phase 5: Transformation

- [ ] Bronze → Silver notebook working
- [ ] Silver → Gold notebook working
- [ ] Data quality validated per layer

### Phase 6: Visualization

- [ ] Semantic Model bound to Gold
- [ ] Reports rendering correctly

### Phase 7: ML (optional)

- [ ] Experiment runs successfully
- [ ] Model registered

### AI & Governance (Optional)

- [ ] Data Agent created (if using)
- [ ] Data Agent bound to appropriate data source (Lakehouse, Warehouse, KQL Database, or Semantic Model)
- [ ] Data Agent greeting and instructions configured
- [ ] Data Agent access permissions set
- [ ] Natural language query returns correct data (test 3-5 representative questions)
- [ ] Agent handles out-of-scope questions gracefully
- [ ] Ontology created (if using) with business terms mapped to data fields
