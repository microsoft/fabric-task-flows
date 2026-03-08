# Validation Checklist

Post-deployment validation for General task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse | Verify permissions |
| Warehouse | Verify permissions; configure schema |
| Eventhouse | Verify permissions; configure KQL databases |
| SQL Database | Verify permissions; configure connection |
| Environment | Configure Spark settings; publish |
| Copy Job | Configure source connections |
| Dataflow Gen2 | Configure data sources; publish |
| Pipeline | Configure activities and schedule |
| Eventstream | Configure event source; start stream |
| Mirrored Database | Verify sync status |
| Notebook | Set default lakehouse; verify environment |
| KQL Queryset | Configure queries |
| Semantic Model | Bind to data source; configure Direct Lake (recommended for Fabric sources) or Import/DirectQuery |
| Report | Verify semantic model binding |
| Real-Time Dashboard | Configure tiles; set refresh |
| Activator | Configure trigger conditions |

## Checklist

### Phase 1: Foundation (Choose applicable)

Storage deployed:
- [ ] Lakehouse (for big data, Spark, ML)
- [ ] Warehouse (for T-SQL, BI)
- [ ] Eventhouse (for real-time, streaming)
- [ ] SQL Database (for OLTP, transactional)
- [ ] Mirrored Database (for external sync)

### Phase 2: Compute Environment

- [ ] Environment created (if using Spark)
- [ ] Variable Library configured (if applicable)
- [ ] Libraries installed

### Phase 3: Ingestion (Choose applicable)

Batch ingestion:
- [ ] Copy Job configured
- [ ] Dataflow Gen2 configured
- [ ] Pipeline configured
- [ ] dbt job configured
- [ ] Airflow job configured

Real-time ingestion:
- [ ] Eventstream configured
- [ ] Custom Stream Connector configured

Mirroring:
- [ ] Mirrored Database syncing
- [ ] Mirrored Dataverse syncing

### Phase 4: Transformation (Choose applicable)

- [ ] Notebooks running
- [ ] Spark Job Definitions scheduled
- [ ] Dataflow Gen2 transforms
- [ ] KQL Querysets configured
- [ ] Stored procedures created

### Phase 5: Semantic & Visualization

- [ ] Semantic Model created
- [ ] Reports rendering
- [ ] Dashboards configured
- [ ] Paginated Reports working
- [ ] Scorecards populated
- [ ] Real-Time Dashboards live

### AI & Governance (Optional)

- [ ] Data Agent created (if using)
- [ ] Data Agent bound to appropriate data source (Lakehouse, Warehouse, KQL Database, or Semantic Model)
- [ ] Data Agent greeting and instructions configured
- [ ] Data Agent access permissions set
- [ ] Natural language query returns correct data (test 3-5 representative questions)
- [ ] Agent handles out-of-scope questions gracefully
- [ ] Ontology created (if using) with business terms mapped to data fields
