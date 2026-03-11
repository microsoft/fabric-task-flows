# Task Flows

Microsoft Fabric task flows - pre-defined architectures for common data scenarios.

## Quick Reference

> Agents: scan this table to identify the right task flow. Only read the detailed section below when you need the full decision table and diagram links.

| Task Flow | Best For | Primary Storage | Key Ingestion | Items |
|-----------|----------|-----------------|---------------|-------|
| `basic-data-analytics` | Simple batch analytics | Warehouse | Copy Job, Dataflow Gen2 | ~11 |
| `medallion` | Layered batch (Bronze/Silver/Gold) | Lakehouse | Pipeline + Notebook | ~15 |
| `lambda` | Batch + real-time combined | Lakehouse + Eventhouse + Warehouse | Eventstream + Pipeline | ~17 |
| `event-analytics` | Real-time streaming focus | Eventhouse | Eventstream | ~15 |
| `event-medallion` | Streaming with medallion layers | Eventhouse + Lakehouse | Eventstream | ~11 |
| `sensitive-data-insights` | Security-focused analytics | Lakehouse | Pipeline + Notebook | ~13 |
| `basic-machine-learning-models` | ML training workflows | Lakehouse | Pipeline + Notebook | ~9 |
| `data-analytics-sql-endpoint` | SQL analytics on Lakehouse | Lakehouse (SQL endpoint) | Copy Job, Pipeline | ~12 |
| `translytical` | Operational with writeback | SQL Database | User Data Functions | ~6 |
| `app-backend` | Application APIs + serverless logic | SQL Database / Cosmos DB | GraphQL, UDFs | ~8 |
| `conversational-analytics` | AI self-service via Data Agents | Lakehouse or Warehouse | (overlay — uses existing ingestion) | ~5 |
| `semantic-governance` | Enterprise vocabulary & knowledge graph | Lakehouse | (overlay — uses existing ingestion) | ~7 |
| `general` | Flexible high-level guidance | Any | Any | varies |

---

---

## Basic Data Analytics

> A basic, step-by-step task flow for batch data analytics.

Follow these steps to obtain your batch data, store it in a warehouse, process the data, build a semantic model, and finally use the results to create quick insights through visualizations.

| Decision | Options | Guide |
|----------|---------|-------|
| Ingestion Method | Copy Job, Dataflow Gen2, Pipeline | [Ingestion Selection](decisions/ingestion-selection.md) |
| Visualization Type | Report, Paginated Report, Scorecard | [Visualization Selection](decisions/visualization-selection.md) |
| Skillset Approach | Low-Code vs Code-First | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [basic-data-analytics](diagrams/basic-data-analytics.md)

---

## Basic Machine Learning Models

> Train machine learning models and generate insights to drive decisions.

Develop and train models based on prepared data and test model accuracy to make decisions with confidence, and gain business insights from predictions.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse (primary for ML) | [Storage Selection](decisions/storage-selection.md) |
| Processing Method | Notebook (primary for ML) | [Processing Selection](decisions/processing-selection.md) |
| Skillset Approach | Low-Code vs Code-First | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [basic-machine-learning-models](diagrams/basic-machine-learning-models.md)

---

## Data Analytics SQL Endpoint

> Select unstructured, semi-structured, or structured data from lakehouse files, and then create reports.

Extract your insights and track metrics from unstructured, semi-structured, and structured data stored in lakehouse files.

| Decision | Options | Guide |
|----------|---------|-------|
| Processing Method | Notebook, Spark Job Definition | [Processing Selection](decisions/processing-selection.md) |
| Visualization Type | Report, Paginated Report, Scorecard | [Visualization Selection](decisions/visualization-selection.md) |

**Diagrams:** [data-analytics-sql-endpoint](diagrams/data-analytics-sql-endpoint.md)

---

## Event Analytics

> Process and analyze real-time data as it is generated to extract insights quickly.

Seamlessly integrate both real-time and time-based data into a unified system. Ingest data from diverse sources to extract valuable insights and promptly respond to changing conditions.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Eventhouse (primary for real-time) | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Eventstream (streaming), Copy Job, Dataflow Gen2, Pipeline (batch) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Visualization Type | Real-Time Dashboard (primary), Report | [Visualization Selection](decisions/visualization-selection.md) |

**Diagrams:** [event-analytics](diagrams/event-analytics.md)

---

## Event Medallion

> A structured approach to ingest, process, and transform large volume streaming and batch data through Bronze, Silver, and Gold layers.

Organize your batch and real-time data into the Bronze, Silver, and Gold layers of a medallion architecture. Build a robust event-driven data processing framework to ensure data integrity and provide real-time insights.

| Decision | Options | Guide |
|----------|---------|-------|
| Ingestion Method | Eventstream (streaming), Copy Job, Pipeline (batch) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Visualization Type | Real-Time Dashboard (live), Report (historical) | [Visualization Selection](decisions/visualization-selection.md) |

**Diagrams:** [event-medallion](diagrams/event-medallion.md)

---

## General

> A high-level data processing task flow that guides you through typical tasks and the items assigned to them.

This task flow guides you through the completion of high-level data processing tasks within Fabric and the items typically assigned to them.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Type | Lakehouse vs Warehouse vs Eventhouse vs SQL Database | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Copy Job vs Dataflow Gen2 vs Pipeline vs Eventstream vs Mirroring | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook vs Spark Job vs Dataflow Gen2 vs KQL vs Stored Procedures | [Processing Selection](decisions/processing-selection.md) |
| Visualization Type | Report vs Dashboard vs Paginated vs Scorecard vs Real-Time Dashboard | [Visualization Selection](decisions/visualization-selection.md) |
| Team Skillset | Code-First [CF] vs Low-Code [LC] | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [general](diagrams/general.md)

---

## Lambda

> Process batch and real-time data in one data process flow.

Analyze your batch and real-time data in a single system efficiently and effectively, while still maintaining a clear separation between the two processing modes.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse (batch), Warehouse (serving), Eventhouse (real-time) | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Copy Job, Pipeline (batch), Eventstream (streaming) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook, Spark Job Definition, KQL Queryset | [Processing Selection](decisions/processing-selection.md) |

**Diagrams:** [lambda](diagrams/lambda.md)

---

## Medallion

> Organize and improve data progressively as it moves through each layer.

Organize data in a lakehouse or warehouse while progressively improving its structure and quality through each layer, from Bronze to Silver to Gold, resulting in high-quality data that is easy to analyze.

| Decision | Options | Guide |
|----------|---------|-------|
| Gold Layer Storage | Lakehouse vs Warehouse | [Storage Selection](decisions/storage-selection.md#gold-layer-decision) |
| Ingestion Method | Copy Job vs Dataflow Gen2 vs Pipeline vs Eventstream | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook vs Spark Job Definition | [Processing Selection](decisions/processing-selection.md) |
| Team Skillset | Code-First [CF] vs Low-Code [LC] | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [medallion](diagrams/medallion.md)

---

## Sensitive Data Insights

> Process and analyze your sensitive data.

Keep your data more secure by applying security features and access controls to your sensitive data while processing and performing analysis tasks. Apply strict access permissions while performing analytics.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse (raw/masked), Warehouse (aggregated) | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Copy Job, Dataflow Gen2, Pipeline (with encryption) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook, Spark Job Definition (with data masking) | [Processing Selection](decisions/processing-selection.md) |

**Diagrams:** [sensitive-data-insights](diagrams/sensitive-data-insights.md)

---

## Translytical

> Improve your decision-making and operational efficiency by automating actions and enabling data writeback directly within your Power BI reports.

Create Fabric User data functions and other items to store data, update records, send dynamic notifications, and trigger workflows across systems.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | SQL Database (OLTP-capable with read/write transactions) | [Storage Selection](decisions/storage-selection.md) |

**Diagrams:** [translytical](diagrams/translytical.md)

---

## App Backend

> Build application backends on Microsoft Fabric — transactional databases, GraphQL APIs, serverless functions, and optional analytics.

Create a transactional database, expose it through a GraphQL API, add serverless business logic with User Data Functions, and optionally layer on analytics with Semantic Models and AI-powered Data Agents.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Type | SQL Database, SQL Database + Cosmos DB Mirroring | [Storage Selection](decisions/storage-selection.md) |
| API Layer | GraphQL API, User Data Functions (REST), Direct Connection | [API Selection](decisions/api-selection.md) |
| Parameterization | Variable Library, parameter.yml, Environment Variables | [Parameterization Selection](decisions/parameterization-selection.md) |
| Visualization Type | Report, Data Agent | [Visualization Selection](decisions/visualization-selection.md) |
| Skillset Approach | Code-First (primary for this flow) | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [app-backend](diagrams/app-backend.md)

---

## Conversational Analytics

> Enable non-technical users to query data through natural language using AI-powered data agents.

Build on top of existing data pipelines by adding a semantic model and an AI-powered data agent. Non-technical users can ask questions in natural language and get answers from governed, modeled data — no report building or query writing required.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse, Warehouse (usually pre-existing from upstream task flow) | [Storage Selection](decisions/storage-selection.md) |
| Semantic Model Design | Direct Lake, Import, DirectQuery | [Visualization Selection](decisions/visualization-selection.md) |
| Agent Configuration | Data scope, access controls, greeting prompts | (Portal configuration) |
| Governance Layer | Ontology for business vocabulary (optional) | (Portal configuration) |
| Skillset Approach | Low-Code (primary — agent + semantic model are UI-driven) | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [conversational-analytics](diagrams/conversational-analytics.md)

---

## Semantic Governance

> Build a unified business vocabulary and knowledge graph for enterprise-wide data governance.

Define business terms, build a knowledge graph of entity relationships, and connect the governance vocabulary to physical data through semantic models. This flow adds an enterprise governance layer on top of existing data pipelines.

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse, Warehouse (usually pre-existing from upstream task flow) | [Storage Selection](decisions/storage-selection.md) |
| Ontology Scope | Single-domain, Cross-domain, Enterprise-wide | (Define based on governance requirements) |
| Graph Modeling | Entity types, edge types, traversal patterns | (Portal configuration) |
| Consumption Layer | Data Agent (conversational), Report (dashboards), Both | [Visualization Selection](decisions/visualization-selection.md) |
| External Integration | Microsoft Purview (catalog/lineage), Azure OpenAI (AI context) | (Optional — configure per environment) |

**Diagrams:** [semantic-governance](diagrams/semantic-governance.md)
