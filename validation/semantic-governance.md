# Validation Checklist

Post-deployment validation for Semantic Governance task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse | Verify data is populated from upstream task flow |
| Semantic Model | Bind to storage; validate measures and relationships |
| Ontology | Create in Fabric workspace portal; define business terms, domains, relationships |
| Graph Model | Create in Fabric workspace portal; define entity types and edge types |
| Graph Queryset | Create in Fabric workspace portal; author graph queries |
| Data Agent | (Optional) Create and bind to Semantic Model + Ontology |

## Checklist

### Phase 1: Foundation

- [ ] Lakehouse (or Warehouse) exists and contains data
- [ ] Workspace permissions configured for governance team
- [ ] Data sources identified for ontology scope

### Phase 2: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 3: Semantic Model

- [ ] Semantic Model created and bound to storage
- [ ] Key measures and relationships defined
- [ ] Field descriptions populated (these inform the Ontology)
- [ ] Model endorsed (Certified or Promoted) if using endorsement

### Phase 4: Ontology Definition

- [ ] Ontology created in Fabric workspace portal
- [ ] Business domains defined (e.g., Sales, Finance, Operations)
- [ ] Key business terms created with definitions
- [ ] Terms mapped to Semantic Model fields/tables
- [ ] Synonyms and abbreviations documented
- [ ] Domain owners assigned

### Phase 5: Knowledge Graph

- [ ] Graph Model created with entity types and relationships
- [ ] Entity types correspond to ontology business terms
- [ ] Edge types define meaningful relationships (e.g., "reports-to", "sells-in", "part-of")
- [ ] Graph Queryset created with representative queries
- [ ] Graph queries return expected traversal results
- [ ] Graph relationships are consistent with Semantic Model relationships

### Phase 6: Governance Validation

- [ ] Business terms are consistent across Ontology and Semantic Model
- [ ] No orphaned terms (terms without data mapping)
- [ ] No unmapped fields (important data fields without business terms)
- [ ] Cross-domain relationships are documented
- [ ] Governance report/dashboard created (if using)
- [ ] Data Agent configured with ontology context (if using)

### Phase 7: External Integration (Optional)

- [ ] Purview catalog synced (if using Microsoft Purview)
- [ ] Data classification labels applied
- [ ] Lineage tracked from source through governance layer
