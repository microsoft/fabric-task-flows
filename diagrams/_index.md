# Deployment Diagrams

> Agents: read this index to find the right diagram. When reading a diagram file, skip to `## Deployment Order` for structured data — the ASCII art above it is for human visualization.

| Task Flow | Diagram | Items | Waves | Primary Storage |
|-----------|---------|-------|-------|-----------------|
| basic-data-analytics | [basic-data-analytics.md](basic-data-analytics.md) | 9 | 6 | Warehouse |
| medallion | [medallion.md](medallion.md) | 13 | 7 | Lakehouse (Bronze/Silver/Gold) |
| lambda | [lambda.md](lambda.md) | 15 | 7 | Lakehouse + Eventhouse + Warehouse |
| event-analytics | [event-analytics.md](event-analytics.md) | 13 | 5 | Eventhouse |
| event-medallion | [event-medallion.md](event-medallion.md) | 9 | 5 | Eventhouse + Lakehouse |
| sensitive-data-insights | [sensitive-data-insights.md](sensitive-data-insights.md) | 11 | 6 | Lakehouse |
| basic-machine-learning-models | [basic-machine-learning-models.md](basic-machine-learning-models.md) | 7 | 7 | Lakehouse |
| data-analytics-sql-endpoint | [data-analytics-sql-endpoint.md](data-analytics-sql-endpoint.md) | 10 | 4 | Lakehouse (SQL endpoint) |
| translytical | [translytical.md](translytical.md) | 4 | 4 | SQL Database |
| app-backend | [app-backend.md](app-backend.md) | 8 | 4 | SQL Database / Cosmos DB |
| conversational-analytics | [conversational-analytics.md](conversational-analytics.md) | 5 | 4 | Lakehouse or Warehouse |
| semantic-governance | [semantic-governance.md](semantic-governance.md) | 7 | 6 | Lakehouse |
| general | [general.md](general.md) | varies | varies | Any |
