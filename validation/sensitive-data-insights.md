# Validation Checklist

Post-deployment validation for Sensitive Data Insights task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse (raw) | Configure strict permissions; enable audit logging |
| Lakehouse (masked) | Configure restricted access |
| Warehouse | Configure RLS/CLS; verify aggregation only |
| Environment | Configure isolated compute; restrict network |
| Copy Job | Use managed identity; verify encryption |
| Dataflow Gen2 | Configure masking transforms |
| Pipeline | Configure secure orchestration |
| Notebook | Implement masking logic; PII redaction |
| Spark Job Def | Configure scheduled anonymization |
| Semantic Model | Configure RLS/OLS rules |
| Report | Verify security inheritance |

## Checklist

### Phase 1: Foundation (Secured)

- [ ] Raw Lakehouse created with strict permissions
- [ ] Masked Lakehouse created with restricted access
- [ ] Warehouse created with aggregation-only data
- [ ] Audit logging enabled on all storage

### Phase 2: Compute Environment (Isolated)

- [ ] Environment created
- [ ] Network restrictions configured
- [ ] Managed identity configured

### Phase 3: Secure Ingestion

- [ ] Ingestion method configured:
  - [ ] Managed identity used (no secrets in code)
  - [ ] Encryption in transit verified
  - [ ] Source connection secured
- [ ] Data flowing to raw Lakehouse

### Phase 4: Secure Transformation

- [ ] Masking/anonymization logic implemented:
  - [ ] PII columns identified
  - [ ] Hashing/tokenization applied
  - [ ] Redaction configured
- [ ] Anonymized data in masked Lakehouse
- [ ] Aggregated data in Warehouse

### Phase 5: Secure Visualization

- [ ] Semantic Model created
- [ ] Row-Level Security (RLS) configured
- [ ] Object-Level Security (OLS) configured
- [ ] Reports render correctly per user role
- [ ] Security inheritance verified

### Security Validation

- [ ] No PII visible in aggregated layer
- [ ] RLS blocks unauthorized rows
- [ ] OLS hides sensitive columns
- [ ] Audit logs capturing access
- [ ] Managed identities used throughout
