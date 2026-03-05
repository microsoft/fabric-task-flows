# Validation Checklist

Post-deployment validation for Lambda task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse | Verify permissions |
| Warehouse | Verify permissions; run initial DDL |
| Eventhouse | Configure retention policies |
| Environment | Configure Spark settings; publish |
| Copy Job | Configure batch source connections |
| Eventstream | Configure real-time source (Event Hub, etc.) |
| Notebook | Set default lakehouse |
| KQL Queryset | Deploy materialized views |
| Semantic Model | Bind to Warehouse; configure Direct Lake (recommended) or Import/DirectQuery |
| Real-Time Dashboard | Build dashboard tiles |
| Activator | Configure alert rules |

## Checklist

### Phase 1: Foundation

- [ ] Lakehouse(s) created (batch layer)
- [ ] Warehouse created (gold layer)
- [ ] Eventhouse created (speed layer)

### Phase 2: Environment

- [ ] Environment created and published

### Phase 3: Ingestion

- [ ] Batch ingestion working (Copy Job / Pipeline)
- [ ] Real-time ingestion working (Eventstream)

### Phase 4: Transformation

- [ ] Batch notebooks running
- [ ] KQL queries processing stream data

### Phase 5: Serving Layer

- [ ] Semantic Model bound to batch data
- [ ] Reports rendering batch views
- [ ] Real-Time Dashboard showing live data

### Phase 6: Monitoring & ML

- [ ] Activator configured for both layers
- [ ] ML models registered and scoring
