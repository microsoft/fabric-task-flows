# Deployment Diagrams

> **Agents: Use `_shared/registry/deployment-order.json` for programmatic access to deployment orders.** The markdown tables below are for human visualization.

For deterministic deployment ordering, load the JSON registry:
```python
from deployment_loader import get_deployment_items
items = get_deployment_items("medallion")  # Returns list of deployment items
```

| Task Flow | Diagram | Items | Waves | Primary Storage |
|-----------|---------|-------|-------|-----------------|
| basic-data-analytics | [basic-data-analytics.md](basic-data-analytics.md) | 11 | 6 | Warehouse |
| medallion | [medallion.md](medallion.md) | 15 | 7 | Lakehouse (Bronze/Silver/Gold) |
| lambda | [lambda.md](lambda.md) | 17 | 7 | Lakehouse + Eventhouse + Warehouse |
| event-analytics | [event-analytics.md](event-analytics.md) | 15 | 5 | Eventhouse |
| event-medallion | [event-medallion.md](event-medallion.md) | 11 | 5 | Eventhouse + Lakehouse |
| sensitive-data-insights | [sensitive-data-insights.md](sensitive-data-insights.md) | 13 | 6 | Lakehouse |
| basic-machine-learning-models | [basic-machine-learning-models.md](basic-machine-learning-models.md) | 9 | 7 | Lakehouse |
| data-analytics-sql-endpoint | [data-analytics-sql-endpoint.md](data-analytics-sql-endpoint.md) | 12 | 4 | Lakehouse (SQL endpoint) |
| translytical | [translytical.md](translytical.md) | 6 | 4 | SQL Database |
| app-backend | [app-backend.md](app-backend.md) | 8 | 4 | SQL Database / Cosmos DB |
| conversational-analytics | [conversational-analytics.md](conversational-analytics.md) | 5 | 4 | Lakehouse or Warehouse |
| semantic-governance | [semantic-governance.md](semantic-governance.md) | 7 | 6 | Lakehouse |
| general | [general.md](general.md) | varies | varies | Any |
