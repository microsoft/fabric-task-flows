# Validation Checklist

Post-deployment validation for Translytical task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| SQL Database | Verify permissions; configure schema for writeback |
| Semantic Model | Bind to SQL Database; configure Direct Lake (via OneLake mirroring) or DirectQuery (for live OLTP data) |
| Report | Enable writeback features; configure data entry |
| User Data Functions | Deploy functions; configure triggers |

## Checklist

### Phase 1: Foundation (Transactional Storage)

- [ ] SQL Database created
- [ ] Tables configured for read/write
- [ ] Write permissions granted to app identity
- [ ] Schema supports writeback scenario

### Phase 2: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 3: Semantic Layer

- [ ] Semantic Model created
- [ ] Connected to SQL Database
- [ ] DirectQuery mode configured (for real-time)
- [ ] Relationships defined
- [ ] Measures created

### Phase 4: Visualization (Writeback)

- [ ] Report created
- [ ] Writeback features enabled
- [ ] Data entry forms configured (if applicable)
- [ ] Write operations working
- [ ] User actions triggering updates

### Phase 5: Development (Actions)

- [ ] User Data Functions deployed:
  - [ ] Write to SQL function working
  - [ ] Notification function working (if applicable)
  - [ ] Workflow trigger function working (if applicable)
- [ ] Functions callable from report
- [ ] Writeback persisting to SQL Database

### Writeback Validation

- [ ] Users can enter data in reports
- [ ] Entered data persists to SQL Database
- [ ] Changes visible on report refresh
- [ ] Notifications triggering (if configured)
- [ ] Downstream workflows executing (if configured)

### AI & Governance (Optional)

- [ ] Data Agent created (if using)
- [ ] Data Agent bound to appropriate data source (Lakehouse, Warehouse, KQL Database, or Semantic Model)
- [ ] Data Agent greeting and instructions configured
- [ ] Data Agent access permissions set
- [ ] Natural language query returns correct data (test 3-5 representative questions)
- [ ] Agent handles out-of-scope questions gracefully
- [ ] Ontology created (if using) with business terms mapped to data fields
