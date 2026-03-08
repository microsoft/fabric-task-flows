# Validation Checklist

Post-deployment validation for Conversational Analytics task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Storage (Lakehouse/Warehouse) | Verify data is populated from upstream task flow |
| Semantic Model | Bind to storage; validate measures and relationships |
| Data Agent | Create in Fabric workspace portal; bind to Semantic Model; configure access |
| Ontology | (Optional) Define business terms in Fabric workspace portal |

## Checklist

### Phase 1: Foundation

- [ ] Storage item exists and contains data (Lakehouse or Warehouse)
- [ ] Data is current (ingestion pipeline from upstream task flow is running)
- [ ] Workspace permissions configured for agent consumers

### Phase 2: Variable Library (if parameterization = variable-library)

- [ ] Variable Library item exists in workspace
- [ ] Variables defined for stage-specific configuration
- [ ] Active value set matches current deployment stage
- [ ] Consuming items (Notebooks, Pipelines, Shortcuts) reference the Variable Library

### Phase 3: Semantic Layer

- [ ] Semantic Model created and bound to storage
- [ ] Key measures defined (aggregations, KPIs)
- [ ] Relationships between tables validated
- [ ] Direct Lake mode configured (if using Lakehouse)
- [ ] Data refresh working (if using Import mode)

### Phase 4: Agent Deployment

- [ ] Data Agent created in Fabric workspace portal
- [ ] Agent bound to Semantic Model
- [ ] Agent greeting / instructions configured
- [ ] Access permissions set (who can chat with the agent)
- [ ] Agent published and accessible to end users

### Phase 5: Agent Testing

- [ ] Natural language query returns correct data (test 3-5 representative questions)
- [ ] Agent correctly handles ambiguous questions (asks for clarification)
- [ ] Agent respects data security (row-level security if applicable)
- [ ] Agent handles "I don't know" gracefully (questions outside data scope)
- [ ] Response latency is acceptable for interactive use

### Phase 6: Optional Governance

- [ ] Ontology created (if using) with business terms mapped to semantic model fields
- [ ] Activator alerts configured (if monitoring agent usage patterns)
