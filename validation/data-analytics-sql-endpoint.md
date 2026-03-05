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

### Phase 2: Data Processing

- [ ] Processing method configured:
  - [ ] OPTION A: Notebook (for ad-hoc/development)
  - [ ] OPTION B: Spark Job Definition (for scheduled)
- [ ] Data transformations complete
- [ ] Delta tables populated

### Phase 3: Semantic Layer

- [ ] Semantic Model created
- [ ] Connected to SQL analytics endpoint
- [ ] Relationships defined
- [ ] Measures created
- [ ] Refresh configured

### Phase 4: Visualization

- [ ] Report created and rendering
- [ ] Dashboard configured (if applicable)
- [ ] Paginated Report working (if applicable)
- [ ] Scorecard metrics populated (if applicable)
