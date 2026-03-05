# Task Flows

Microsoft Fabric task flows - pre-defined architectures for common data scenarios.

---

## Basic Data Analytics

> A basic, step-by-step task flow for batch data analytics.

**Tasks:** 4

Follow these steps to obtain your batch data, store it in a warehouse, process the data, build a semantic model, and finally use the results to create quick insights through visualizations.

```
get data ──→ store data ──→ visualize ──→ track data
```

**Workloads:** Data Factory, Data Warehouse, Real-Time Intelligence, Power BI

**Items:** Activator, Copy job, Dashboard, Dataflow Gen2, Paginated Report, Pipeline, Report, Scorecard, Semantic model, Warehouse

| Decision | Options | Guide |
|----------|---------|-------|
| Ingestion Method | Copy Job, Dataflow Gen2, Pipeline | [Ingestion Selection](decisions/ingestion-selection.md) |
| Visualization Type | Report, Dashboard, Paginated Report, Scorecard | [Visualization Selection](decisions/visualization-selection.md) |
| Skillset Approach | Low-Code vs Code-First | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [basic-data-analytics](diagrams/basic-data-analytics.md) | **Validation:** [basic-data-analytics](validation/basic-data-analytics.md)

---

## Basic Machine Learning Models

> Train machine learning models and generate insights to drive decisions.

**Tasks:** 6

Develop and train models based on prepared data and test model accuracy to make decisions with confidence, and gain business insights from predictions.

```
              ┌──→ analyze and train data ──→ analyze and train data ──→ analyze and train data
              │
store data ──┤
              │
              └──→ visualize
```

**Workloads:** Data Engineering, Data Science, Power BI

**Items:** Environment, Experiment, Lakehouse, ML model, Notebook, Report

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse (primary for ML) | [Storage Selection](decisions/storage-selection.md) |
| Processing Method | Notebook (primary for ML) | [Processing Selection](decisions/processing-selection.md) |
| Skillset Approach | Low-Code vs Code-First | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [basic-machine-learning-models](diagrams/basic-machine-learning-models.md) | **Validation:** [basic-machine-learning-models](validation/basic-machine-learning-models.md)

---

## Data Analytics SQL Endpoint

> Select unstructured, semi-structured, or structured data from lakehouse files, and then create reports.

**Tasks:** 4

Extract your insights and track metrics from unstructured, semi-structured, and structured data stored in lakehouse files.

```
store data ──→ prepare data ──→ store data ──→ visualize
```

**Workloads:** Data Engineering, Data Science, Data Warehouse, Power BI

**Items:** Dashboard, Lakehouse, Notebook, Paginated Report, Report, Scorecard, Semantic model, Spark Job Definition, SQL analytics endpoint

| Decision | Options | Guide |
|----------|---------|-------|
| Processing Method | Notebook, Spark Job Definition | [Processing Selection](decisions/processing-selection.md) |
| Visualization Type | Report, Dashboard, Paginated Report, Scorecard | [Visualization Selection](decisions/visualization-selection.md) |

**Diagrams:** [data-analytics-sql-endpoint](diagrams/data-analytics-sql-endpoint.md) | **Validation:** [data-analytics-sql-endpoint](validation/data-analytics-sql-endpoint.md)

---

## Event Analytics

> Process and analyze real-time data as it is generated to extract insights quickly.

**Tasks:** 6

Seamlessly integrate both real-time and time-based data into a unified system. Ingest data from diverse sources to extract valuable insights and promptly respond to changing conditions.

```
get data ──→ track data ──┐
                          │
                          ├──→ store data ──┬──→ visualize
                          │                 │
get data ─────────────────┘                 └──→ analyze and train data
```

**Workloads:** Data Engineering, Data Factory, Data Science, Real-Time Intelligence, Power BI

**Items:** Activator, Copy job, Dashboard, Dataflow Gen2, Environment, Eventhouse, Eventstream, Experiment, KQL Queryset, ML model, Notebook, Pipeline, Real-Time Dashboard, Report, Spark Job Definition

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Eventhouse (primary for real-time) | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Eventstream (streaming), Copy Job, Dataflow Gen2, Pipeline (batch) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Visualization Type | Real-Time Dashboard (primary), Report | [Visualization Selection](decisions/visualization-selection.md) |

**Diagrams:** [event-analytics](diagrams/event-analytics.md) | **Validation:** [event-analytics](validation/event-analytics.md)

---

## Event Medallion

> A structured approach to ingest, process, and transform large volume streaming and batch data through Bronze, Silver, and Gold layers.

**Tasks:** 10

Organize your batch and real-time data into the Bronze, Silver, and Gold layers of a medallion architecture. Build a robust event-driven data processing framework to ensure data integrity and provide real-time insights.

```
get data ──┐
           ├──→ store data ──→ prepare data ──→ store data ──→ prepare data ──→ store data ──┬──→ visualize
get data ──┘                                                                                 ├──→ track data
                                                                                             └──→ visualize
```

**Workloads:** Data Factory, Real-Time Intelligence, Power BI

**Items:** Activator, Copy job, Eventhouse, Eventstream, KQL Queryset, Pipeline, Real-Time Dashboard, Report

| Decision | Options | Guide |
|----------|---------|-------|
| Ingestion Method | Eventstream (streaming), Copy Job, Pipeline (batch) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Visualization Type | Real-Time Dashboard (live), Report (historical) | [Visualization Selection](decisions/visualization-selection.md) |

**Diagrams:** [event-medallion](diagrams/event-medallion.md) | **Validation:** [event-medallion](validation/event-medallion.md)

---

## General

> A high-level data processing task flow that guides you through typical tasks and the items assigned to them.

**Tasks:** 10

This task flow guides you through the completion of high-level data processing tasks within Fabric and the items typically assigned to them.

```
get data ──────→ store data ──→ analyze and train data ──→ develop ──→ govern data
                    ↑
mirror data ────────┘
                 store data ──→ prepare data ──→ visualize ──→ distribute data
                                     │
                                     └──→ track data ──→ govern data
```

**Workloads:** Data Engineering, Data Factory, Data Science, Data Warehouse, Databases, Graph, IQ, Real-Time Intelligence, Power BI

**Items:** Activator, Anomaly detector, Apache Airflow job, API for GraphQL, Azure Data Factory, Blueprint, Business Event Topic, Copy job, Cosmos DB database, Custom stream connector, Dashboard, Data agent, Dataflow Gen1, Dataflow Gen2, Dataflow Gen2 (CI/CD), Datamart, dbt job, Deployment Plan, Digital Twin Builder, Environment, Event Schema Set, Eventhouse, Eventstream, Experiment, Exploration, Graph model, Graph queryset, KQL Database, KQL Queryset, Lakehouse, Map, Mirrored Azure Databricks catalog, Mirrored catalog, Mirrored database, Mirrored Dataverse, ML model, Notebook, Ontology, Operations agent, Org app, Paginated Report, Pipeline, Planning, PostgreSQL Database, Real-Time Dashboard, Report, Scorecard, Semantic model, Snowflake database, Spark Job Definition, SQL database, User data functions, Variable library, Warehouse

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Type | Lakehouse vs Warehouse vs Eventhouse vs SQL Database | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Copy Job vs Dataflow Gen2 vs Pipeline vs Eventstream vs Mirroring | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook vs Spark Job vs Dataflow Gen2 vs KQL vs Stored Procedures | [Processing Selection](decisions/processing-selection.md) |
| Visualization Type | Report vs Dashboard vs Paginated vs Scorecard vs Real-Time Dashboard | [Visualization Selection](decisions/visualization-selection.md) |
| Team Skillset | Code-First [CF] vs Low-Code [LC] | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [general](diagrams/general.md) | **Validation:** [general](validation/general.md)

---

## Lambda

> Process batch and real-time data in one data process flow.

**Tasks:** 11

Analyze your batch and real-time data in a single system efficiently and effectively, while still maintaining a clear separation between the two processing modes.

```
                          ┌──→ store data ──→ visualize ──┐
                          │                               │
get data ──→ track data ──┤                               ├──→ visualize ──→ track data
                          │                               │
                          └───────────────────────────────┘

get data ──→ store data ──→ prepare data ──→ store data ──→ analyze and train data
```

**Workloads:** Data Engineering, Data Factory, Data Science, Data Warehouse, Real-Time Intelligence, Power BI

**Items:** Activator, Copy job, Dashboard, Dataflow Gen2, Environment, Eventhouse, Eventstream, Experiment, KQL Queryset, Lakehouse, ML model, Notebook, Pipeline, Real-Time Dashboard, Report, Spark Job Definition, Warehouse

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse (batch), Warehouse (serving), Eventhouse (real-time) | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Copy Job, Pipeline (batch), Eventstream (streaming) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook, Spark Job Definition, KQL Queryset | [Processing Selection](decisions/processing-selection.md) |

**Diagrams:** [lambda](diagrams/lambda.md) | **Validation:** [lambda](validation/lambda.md)

---

## Medallion

> Organize and improve data progressively as it moves through each layer.

**Tasks:** 9

Organize data in a lakehouse or warehouse while progressively improving its structure and quality through each layer, from Bronze to Silver to Gold, resulting in high-quality data that is easy to analyze.

```
get data ──┐
           ├──→ store data ──→ prepare data ──→ store data ──→ prepare data ──→ store data ──┬──→ visualize
get data ──┘                                                                                 │
                                                                                             └──→ analyze and train data
```

**Workloads:** Data Engineering, Data Factory, Data Science, Data Warehouse, Real-Time Intelligence, Power BI

**Items:** Copy job, Dashboard, Dataflow Gen2, Environment, Eventstream, Experiment, Lakehouse, ML model, Notebook, Pipeline, Report, Spark Job Definition, Warehouse

| Decision | Options | Guide |
|----------|---------|-------|
| Gold Layer Storage | Lakehouse vs Warehouse | [Storage Selection](decisions/storage-selection.md#gold-layer-decision) |
| Ingestion Method | Copy Job vs Dataflow Gen2 vs Pipeline vs Eventstream | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook vs Spark Job Definition | [Processing Selection](decisions/processing-selection.md) |
| Team Skillset | Code-First [CF] vs Low-Code [LC] | [Skillset Selection](decisions/skillset-selection.md) |

**Diagrams:** [medallion](diagrams/medallion.md) | **Validation:** [medallion](validation/medallion.md)

---

## Sensitive Data Insights

> Process and analyze your sensitive data.

**Tasks:** 9

Keep your data more secure by applying security features and access controls to your sensitive data while processing and performing analysis tasks. Apply strict access permissions while performing analytics.

```
                          ┌──→ get data ──→ store data ──→ visualize
                          │
get data ──→ store data ──┤
                          │
                          └──→ prepare data ──→ store data ──┬──→ visualize
                                                             │
                                                             └──→ analyze and train data
```

**Workloads:** Data Engineering, Data Factory, Data Science, Data Warehouse, Power BI

**Items:** Copy job, Dashboard, Dataflow Gen2, Environment, Experiment, Lakehouse, ML model, Notebook, Pipeline, Report, Spark Job Definition, Warehouse

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | Lakehouse (raw/masked), Warehouse (aggregated) | [Storage Selection](decisions/storage-selection.md) |
| Ingestion Method | Copy Job, Dataflow Gen2, Pipeline (with encryption) | [Ingestion Selection](decisions/ingestion-selection.md) |
| Processing Method | Notebook, Spark Job Definition (with data masking) | [Processing Selection](decisions/processing-selection.md) |

**Diagrams:** [sensitive-data-insights](diagrams/sensitive-data-insights.md) | **Validation:** [sensitive-data-insights](validation/sensitive-data-insights.md)

---

## Translytical

> Improve your decision-making and operational efficiency by automating actions and enabling data writeback directly within your Power BI reports.

**Tasks:** 3

Create Fabric User data functions and other items to store data, update records, send dynamic notifications, and trigger workflows across systems.

```
store data ──→ visualize ──→ develop
```

**Workloads:** Data Engineering, Data Factory, Databases, Power BI

**Items:** Report, Semantic model, SQL database, User data functions

| Decision | Options | Guide |
|----------|---------|-------|
| Storage Solution | SQL Database (OLTP-capable with read/write transactions) | [Storage Selection](decisions/storage-selection.md) |

**Diagrams:** [translytical](diagrams/translytical.md) | **Validation:** [translytical](validation/translytical.md)
