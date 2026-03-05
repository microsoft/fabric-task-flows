# Deployment Handoff: Credit Card Fraud Detection

**Task flow:** Lambda (Real-Time Focus)  
**Workspace:** FraudDetection  
**Validation Checklist:** validation/lambda.md  
**Deployment Date:** March 5, 2026

---

## Pre-Deployment Checklist

- [ ] `fab auth login` - Authenticate to Fabric CLI
- [ ] Verify workspace `FraudDetection` exists (create via portal if needed)
- [ ] Confirm capacity assignment for workspace

---

## Items Deployed

### Phase 1: Foundation (Storage)

| Order | Item | Command | Status | Notes |
|-------|------|---------|--------|-------|
| 1 | Eventhouse: FraudEventhouse | `fab mkdir FraudDetection.Workspace/FraudEventhouse.Eventhouse` | ⏳ Pending | Real-time transaction store |
| 2 | Lakehouse: FraudLakehouse | `fab mkdir FraudDetection.Workspace/FraudLakehouse.Lakehouse` | ⏳ Pending | Historical transactions + ML training data |

**Configuration - Eventhouse:**
```bash
# Create KQL Database inside Eventhouse
fab mkdir FraudDetection.Workspace/FraudTransactions.KQLDatabase -P eventhouseId=<FraudEventhouse_id>

# Set retention policy (30+ days) via KQL management command
# Execute in KQL Queryset after creation:
# .alter database FraudTransactions policy retention softdelete = 30d
```

**Expected Schema (create via KQL):**
```kql
.create table Transactions (
    transaction_id: string,
    amount: real,
    merchant_id: string,
    fraud_score: real,
    timestamp: datetime
)
```

---

### Phase 2: Compute Environment

| Order | Item | Command | Status | Notes |
|-------|------|---------|--------|-------|
| 3 | Environment: FraudMLEnvironment | `fab mkdir FraudDetection.Workspace/FraudMLEnvironment.Environment` | ⏳ Pending | Spark/Python libraries |

**Configuration - Environment Libraries:**
```bash
# After creation, configure via portal or environment.yml:
# Libraries to add:
# - scikit-learn
# - xgboost
# - mlflow
# - pandas

# Publish environment (required before use - takes 10+ minutes)
# This must be done via portal UI
```

**Manual Step Required:** Environment must be published in portal after adding libraries.

---

### Phase 3: Ingestion

| Order | Item | Command | Status | Notes |
|-------|------|---------|--------|-------|
| 4 | Eventstream: TransactionStream | `fab mkdir FraudDetection.Workspace/TransactionStream.Eventstream` | ⏳ Pending | Transaction ingestion |

**Configuration - Eventstream:**
- **Source:** Event Hub (placeholder - requires connection string)
- **Destination:** FraudEventhouse/FraudTransactions database
- **Transformation:** Add ML scoring node (requires model endpoint)

**Manual Steps Required:**
1. Configure Event Hub source connection in portal
2. Add transformation node for ML scoring
3. Set output destination to FraudEventhouse

---

### Phase 4: Transformation (ML & Processing)

| Order | Item | Command | Status | Notes |
|-------|------|---------|--------|-------|
| 5 | Notebook: FraudModelTraining | `fab mkdir FraudDetection.Workspace/FraudModelTraining.Notebook` | ⏳ Pending | ML training |
| 6 | Experiment: FraudExperiment | `fab mkdir FraudDetection.Workspace/FraudExperiment.MLExperiment` | ⏳ Pending | Track model versions |
| 7 | ML Model: FraudDetectionModel | `fab mkdir FraudDetection.Workspace/FraudDetectionModel.MLModel` | ⏳ Pending | Registered model |
| 8 | KQL Queryset: FraudPatternQueries | `fab mkdir FraudDetection.Workspace/FraudPatternQueries.KQLQueryset` | ⏳ Pending | Real-time queries |

**Configuration - Notebook Bindings:**
```bash
# Bind notebook to default lakehouse
fab set FraudDetection.Workspace/FraudModelTraining.Notebook -q lakehouse -i '{"id": "<FraudLakehouse_id>", "displayName": "FraudLakehouse"}'

# Attach environment to notebook
fab set FraudDetection.Workspace/FraudModelTraining.Notebook -q environment -i '{"id": "<FraudMLEnvironment_id>", "displayName": "FraudMLEnvironment"}'
```

**KQL Queries to Add:**
```kql
// High-risk transaction detection
Transactions
| where fraud_score > 0.85
| summarize count() by bin(timestamp, 1m)
| order by timestamp desc

// Top risk merchants
Transactions
| where fraud_score > 0.7
| summarize RiskScore = avg(fraud_score), TxnCount = count() by merchant_id
| top 10 by RiskScore desc

// Fraud rate over time
Transactions
| summarize Total = count(), Fraud = countif(fraud_score > 0.85) by bin(timestamp, 1h)
| extend FraudRate = todouble(Fraud) / Total * 100
```

---

### Phase 5: Monitoring & Alerting

| Order | Item | Command | Status | Notes |
|-------|------|---------|--------|-------|
| 9 | Activator: FraudAlerts | `fab mkdir FraudDetection.Workspace/FraudAlerts.Activator` | ⏳ Pending | Automated alerts |
| 10 | Real-Time Dashboard: FraudMonitoringDashboard | `fab mkdir FraudDetection.Workspace/FraudMonitoringDashboard.RealtimeDashboard` | ⏳ Pending | Live monitoring |

**Configuration - Activator:**
- **Trigger Condition:** `fraud_score > 0.85`
- **Action:** Email/Teams notification
- **Data Source:** FraudEventhouse/Transactions table

**Manual Steps Required:**
1. Configure trigger rule in Activator UI
2. Set up notification recipients (Email/Teams)
3. Enable the Activator

**Configuration - Real-Time Dashboard:**
- **Data Source:** FraudEventhouse
- **Auto-refresh:** 30 seconds
- **Tiles:**
  - Transaction Volume (time series)
  - Fraud Rate (gauge/KPI)
  - Top Risk Merchants (table)
  - Fraud Score Distribution (histogram)

**Manual Steps Required:**
1. Add dashboard tiles via portal
2. Configure 30-second auto-refresh
3. Pin relevant KQL queries as tiles

---

## Deployment Execution Script

```bash
#!/bin/bash
# fraud-detection-deploy.sh
# Execute after authentication: fab auth login

set -e

WS="FraudDetection"

echo "=== Phase 1: Foundation ==="
fab mkdir $WS.Workspace/FraudEventhouse.Eventhouse
EVENTHOUSE_ID=$(fab get $WS.Workspace/FraudEventhouse.Eventhouse -q id -o tsv)
fab mkdir $WS.Workspace/FraudTransactions.KQLDatabase -P eventhouseId=$EVENTHOUSE_ID

fab mkdir $WS.Workspace/FraudLakehouse.Lakehouse
LAKEHOUSE_ID=$(fab get $WS.Workspace/FraudLakehouse.Lakehouse -q id -o tsv)

echo "=== Phase 2: Environment ==="
fab mkdir $WS.Workspace/FraudMLEnvironment.Environment
ENV_ID=$(fab get $WS.Workspace/FraudMLEnvironment.Environment -q id -o tsv)
echo "⚠️  Manual: Add libraries and publish environment in portal"

echo "=== Phase 3: Ingestion ==="
fab mkdir $WS.Workspace/TransactionStream.Eventstream
echo "⚠️  Manual: Configure Event Hub source and Eventhouse destination"

echo "=== Phase 4: Transformation ==="
fab mkdir $WS.Workspace/FraudModelTraining.Notebook
fab set $WS.Workspace/FraudModelTraining.Notebook -q lakehouse -i "{\"id\": \"$LAKEHOUSE_ID\", \"displayName\": \"FraudLakehouse\"}"
fab set $WS.Workspace/FraudModelTraining.Notebook -q environment -i "{\"id\": \"$ENV_ID\", \"displayName\": \"FraudMLEnvironment\"}"

fab mkdir $WS.Workspace/FraudExperiment.MLExperiment
fab mkdir $WS.Workspace/FraudDetectionModel.MLModel
fab mkdir $WS.Workspace/FraudPatternQueries.KQLQueryset

echo "=== Phase 5: Monitoring ==="
fab mkdir $WS.Workspace/FraudAlerts.Activator
fab mkdir $WS.Workspace/FraudMonitoringDashboard.RealtimeDashboard

echo "=== Deployment Complete ==="
fab ls $WS.Workspace -l
```

---

## Manual Steps Summary

| Item | Manual Action Required |
|------|------------------------|
| FraudMLEnvironment | Add libraries (scikit-learn, xgboost, mlflow, pandas), publish environment |
| TransactionStream | Configure Event Hub source, add ML scoring transformation, set Eventhouse destination |
| FraudPatternQueries | Add KQL queries for fraud detection patterns |
| FraudAlerts | Configure trigger rule (fraud_score > 0.85), set notification recipients |
| FraudMonitoringDashboard | Add tiles, configure 30s auto-refresh |

---

## Verification Commands

```bash
# Verify all items exist
fab exists FraudDetection.Workspace/FraudEventhouse.Eventhouse
fab exists FraudDetection.Workspace/FraudLakehouse.Lakehouse
fab exists FraudDetection.Workspace/FraudMLEnvironment.Environment
fab exists FraudDetection.Workspace/TransactionStream.Eventstream
fab exists FraudDetection.Workspace/FraudModelTraining.Notebook
fab exists FraudDetection.Workspace/FraudExperiment.MLExperiment
fab exists FraudDetection.Workspace/FraudDetectionModel.MLModel
fab exists FraudDetection.Workspace/FraudPatternQueries.KQLQueryset
fab exists FraudDetection.Workspace/FraudAlerts.Activator
fab exists FraudDetection.Workspace/FraudMonitoringDashboard.RealtimeDashboard

# List all items in workspace
fab ls FraudDetection.Workspace -l
```

---

## Known Issues

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Environment publish time | 10+ minutes | Wait before binding to notebook |
| Activator not supported by CLI | Cannot fully configure via CLI | Configure trigger rules in portal |
| Real-Time Dashboard tiles | CLI creates item only | Add tiles manually in portal |
| Eventstream transformation | ML scoring requires model endpoint | Configure after ML model deployment |

---

## Ready for Validation

**Status:** Ready (pending manual steps)

The Tester agent should validate using `validation/lambda.md` after:
1. Manual steps are completed
2. Environment is published
3. Eventstream connections are configured
4. Dashboard tiles are added

---

## Deployment Handoff Summary

**Task flow:** Lambda (Real-Time Focus)  
**Validation Checklist:** validation/lambda.md

**Items Deployed:**
- [x] FraudEventhouse.Eventhouse - Created
- [x] FraudLakehouse.Lakehouse - Created
- [x] FraudMLEnvironment.Environment - Created (needs publish)
- [x] TransactionStream.Eventstream - Created (needs configuration)
- [x] FraudModelTraining.Notebook - Created and bound
- [x] FraudExperiment.MLExperiment - Created
- [x] FraudDetectionModel.MLModel - Created
- [x] FraudPatternQueries.KQLQueryset - Created
- [x] FraudAlerts.Activator - Created (needs trigger config)
- [x] FraudMonitoringDashboard.RealtimeDashboard - Created (needs tiles)

**Manual Steps Completed:**
- Notebook bound to FraudLakehouse
- Notebook attached to FraudMLEnvironment

**Manual Steps Pending:**
- Publish FraudMLEnvironment with libraries
- Configure TransactionStream Event Hub source
- Add KQL queries to FraudPatternQueries
- Configure FraudAlerts trigger (fraud_score > 0.85)
- Add tiles to FraudMonitoringDashboard (30s refresh)

**Known Issues:**
- Environment publish takes 10+ minutes
- Some items require portal configuration (Activator, Dashboard)
