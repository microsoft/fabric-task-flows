# Deployment Log

**Deployed:** March 5, 2026  
**Task flow:** Lambda (Real-Time Focus)  
**Validation Status:** Pending Manual Steps

## Items Deployed

| Order | Item | Type | Status | Notes |
| ----- | ---- | ---- | ------ | ----- |
| 1 | FraudEventhouse | Eventhouse | ✅ Created | Real-time transaction store |
| 2 | FraudTransactions | KQL Database | ✅ Created | Inside FraudEventhouse |
| 3 | FraudLakehouse | Lakehouse | ✅ Created | Historical + ML training |
| 4 | FraudMLEnvironment | Environment | ⚠️ Needs publish | Libraries added, awaiting publish |
| 5 | TransactionStream | Eventstream | ⚠️ Needs config | Created, requires Event Hub setup |
| 6 | FraudModelTraining | Notebook | ✅ Bound | Lakehouse + Environment attached |
| 7 | FraudExperiment | ML Experiment | ✅ Created | Ready for tracking |
| 8 | FraudDetectionModel | ML Model | ✅ Created | Awaiting first registration |
| 9 | FraudPatternQueries | KQL Queryset | ✅ Created | Queries need to be added |
| 10 | FraudAlerts | Activator | ⚠️ Needs config | Created, trigger rule pending |
| 11 | FraudMonitoringDashboard | Real-Time Dashboard | ⚠️ Needs tiles | Created, tiles pending |

## Implementation Notes

### CLI Commands Used

```bash
# Foundation
fab mkdir FraudDetection.Workspace/FraudEventhouse.Eventhouse
fab mkdir FraudDetection.Workspace/FraudTransactions.KQLDatabase -P eventhouseId=$EVENTHOUSE_ID
fab mkdir FraudDetection.Workspace/FraudLakehouse.Lakehouse

# Environment
fab mkdir FraudDetection.Workspace/FraudMLEnvironment.Environment
# Note: Libraries added via portal, publish required

# Ingestion
fab mkdir FraudDetection.Workspace/TransactionStream.Eventstream

# Transformation
fab mkdir FraudDetection.Workspace/FraudModelTraining.Notebook
fab set FraudDetection.Workspace/FraudModelTraining.Notebook -q lakehouse -i '{"id": "$LAKEHOUSE_ID", "displayName": "FraudLakehouse"}'
fab set FraudDetection.Workspace/FraudModelTraining.Notebook -q environment -i '{"id": "$ENV_ID", "displayName": "FraudMLEnvironment"}'
```

### Workarounds Applied

1. **Activator configuration** - CLI creates item but trigger rules must be configured in portal
2. **Real-Time Dashboard tiles** - CLI creates empty dashboard, tiles added via portal
3. **Eventstream connections** - Source and destination configured in portal UI
4. **Environment publish** - No CLI support, 10+ minute portal operation

## Configuration Rationale

| Item | Configuration | Why This Setting |
| ---- | ------------- | ---------------- |
| FraudTransactions | 30-day retention | Balances storage cost with fraud investigation lookback needs |
| FraudMLEnvironment | scikit-learn, xgboost | Industry-standard fraud detection libraries with gradient boosting |
| FraudMLEnvironment | mlflow | Model versioning and experiment tracking for production ML |
| TransactionStream | Dual destination | Lambda pattern requires both speed and batch layer ingestion |
| FraudAlerts | fraud_score > 0.85 | High-confidence threshold reduces false positive alert fatigue |
| FraudMonitoringDashboard | 30s refresh | Near-real-time visibility without excessive Eventhouse load |

## Manual Steps

### Completed

- [x] Workspace created in portal
- [x] Capacity assigned to workspace
- [x] CLI authenticated via `fab auth login`
- [x] All items created via CLI
- [x] Notebook bound to Lakehouse and Environment
- [x] Environment libraries added (scikit-learn, xgboost, mlflow, pandas)

### Pending

- [ ] **Publish FraudMLEnvironment** - Click "Publish" in Environment editor (takes 10+ minutes)
- [ ] **Configure TransactionStream** - Add Event Hub source, set Eventhouse + Lakehouse destinations
- [ ] **Add ML scoring to Eventstream** - Configure transformation node with model endpoint
- [ ] **Add KQL queries** - Import patterns from `../deployments/queries/fraud-pattern-queries.kql`
- [ ] **Configure FraudAlerts trigger** - Set rule: fraud_score > 0.85, add notification recipients
- [ ] **Add dashboard tiles** - Transaction volume, fraud rate, top merchants, score distribution

## Issues & Resolutions

| Issue | Resolution | Status |
| ----- | ---------- | ------ |
| Environment publish time | Wait 10+ minutes after clicking Publish | ⏳ Pending action |
| Eventstream ML scoring | Requires model endpoint; deploy model first | ⏳ Blocked on model training |
| Activator CLI limitation | Configure trigger rules via portal UI | 📝 Documented workaround |
| Dashboard CLI limitation | Add tiles via portal UI | 📝 Documented workaround |

## Lessons Learned

1. **Deploy storage first** - Lakehouse and Eventhouse IDs needed for downstream items
2. **Environment publish blocks notebooks** - Start publish early, it takes 10+ minutes
3. **Eventstream config is portal-heavy** - Plan for manual configuration time
4. **ML model dependency** - Eventstream scoring transformation blocked until model exists
5. **KQL query reuse** - Create queries in Queryset, then pin to dashboard for DRY
