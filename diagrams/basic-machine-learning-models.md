# Basic Machine Learning Models Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   BASIC MACHINE LEARNING MODELS DEPLOYMENT                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Storage + Compute)                                        │
│  ════════════════════════════════════════                                       │
│  Deploy storage and compute together - they form the ML foundation:             │
│                                                                                 │
│  ┌──────────────┐              ┌──────────────┐                                 │
│  │   Lakehouse  │              │ Environment  │                                 │
│  │    [LC]      │              │    [CF]      │                                 │
│  └──────┬───────┘              └──────┬───────┘                                 │
│         │                             │                                         │
│         └──────────────┬──────────────┘                                         │
│                        │                                                        │
│                        ▼                                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: DATA EXPLORATION (Load & Process)                                     │
│  ════════════════════════════════════════════                                   │
│  ┌─────────────────────┐                                                        │
│  │      Notebook       │ ◄── Reads data from Lakehouse                          │
│  │  (01_ExploreData)   │                                                        │
│  │       [CF]          │                                                        │
│  └──────────┬──────────┘                                                        │
│             │                                                                   │
│             ▼                                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: TRAINING (Experiment & Train)                                         │
│  ════════════════════════════════════════                                       │
│  ┌──────────────┐       ┌─────────────────────┐                                 │
│  │  Experiment  │◄──────│      Notebook       │                                 │
│  │    [CF]      │       │  (02_TrainModel)    │                                 │
│  │              │       │       [CF]          │                                 │
│  └──────┬───────┘       └─────────────────────┘                                 │
│         │                                                                       │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: MODEL REGISTRATION                                                    │
│  ════════════════════════════════                                               │
│  ┌──────────────┐                                                               │
│  │   ML Model   │ ◄── Registered from best experiment run                       │
│  │    [CF]      │                                                               │
│  └──────┬───────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: BATCH PREDICTIONS                                                     │
│  ════════════════════════════════                                               │
│  ┌─────────────────────┐       ┌──────────────┐                                 │
│  │      Notebook       │──────►│   Lakehouse  │                                 │
│  │ (03_BatchPredict)   │       │ (predictions)│                                 │
│  │       [CF]          │       │              │                                 │
│  └─────────────────────┘       └──────┬───────┘                                 │
│                                       │                                         │
│                                       ▼                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 6: VISUALIZATION                                                         │
│  ════════════════════════                                                       │
│  ┌──────────────┐                                                               │
│  │    Report    │ ◄── Built on Lakehouse data with predictions                   │
│  │    [LC]      │                                                               │
│  └──────────────┘                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## ML Workflow Decision

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ML WORKFLOW DECISION GUIDE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ Is your data already in a Lakehouse? ─────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  YES ──► Skip ingestion, proceed to exploration notebooks                  │ │
│  │                                                                            │ │
│  │  NO ──► Use Copy Job or Pipeline to load data first                        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ What ML framework will you use? ──────────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  AutoML ──► MLflow autolog captures metrics automatically                  │ │
│  │                                                                            │ │
│  │  Custom ──► Use mlflow.log_metrics() and mlflow.log_model()                │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ How will you deploy the model? ───────────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  Batch scoring ──► Notebook with PREDICT() or model.predict()              │ │
│  │                                                                            │ │
│  │  Real-time ──► Not covered in this task flow (use Azure ML)                 │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
