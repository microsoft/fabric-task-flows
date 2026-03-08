# Validation Checklist

Post-deployment validation for Data Analytics Using SQL Endpoint task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse | Verify permissions; SQL analytics endpoint auto-created |
| Notebook | Set default lakehouse; verify environment attachment |
| Spark Job Definition | Set default lakehouse; configure schedule |
| Semantic Model | Bind to Lakehouse; configure Direct Lake (recommended) or Import/DirectQuery |
| Report | Verify semantic model binding |
| Dashboard | Pin visuals from reports |
| Paginated Report | Configure parameters; verify data source |
| Scorecard | Configure goals and metrics |

## Checklist

### Phase 1: Foundation

- [ ] Lakehouse created
- [ ] SQL analytics endpoint accessible
- [ ] Delta tables created

### Phase 2: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 3: Data Processing

- [ ] Processing method configured:
  - [ ] OPTION A: Notebook (for ad-hoc/development)
  - [ ] OPTION B: Spark Job Definition (for scheduled)
- [ ] Data transformations complete
- [ ] Delta tables populated

### Phase 4: Semantic Layer

- [ ] Semantic Model created
- [ ] Connected to SQL analytics endpoint
- [ ] Relationships defined
- [ ] Measures created
- [ ] Refresh configured

### Phase 5: Visualization

- [ ] Report created and rendering
- [ ] Dashboard configured (if applicable)
- [ ] Paginated Report working (if applicable)
- [ ] Scorecard metrics populated (if applicable)

### AI & Governance (Optional)

- [ ] Data Agent created (if using)
- [ ] Data Agent bound to appropriate data source (Lakehouse, Warehouse, KQL Database, or Semantic Model)
- [ ] Data Agent greeting and instructions configured
- [ ] Data Agent access permissions set
- [ ] Natural language query returns correct data (test 3-5 representative questions)
- [ ] Agent handles out-of-scope questions gracefully
- [ ] Ontology created (if using) with business terms mapped to data fields
