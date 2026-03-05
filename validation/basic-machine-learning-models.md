# Validation Checklist

Post-deployment validation for Basic Machine Learning Models task flow.

## Post-Deployment Manual Steps

| Item Type | Manual Action Required |
|-----------|------------------------|
| Lakehouse | Verify permissions; configure for ML data |
| Environment | Configure Spark settings; install ML libraries; publish |
| Notebook (explore) | Set default lakehouse; verify environment attachment |
| Notebook (train) | Set default lakehouse; configure MLflow tracking |
| Experiment | Verify experiment tracking enabled |
| ML Model | Register best model from experiment |
| Notebook (predict) | Load registered model; set default lakehouse |
| Report | Verify semantic model binding; check predictions data |

## Checklist

### Phase 1: Foundation

- [ ] Lakehouse created
- [ ] Environment created and published
- [ ] ML libraries installed (sklearn, mlflow, etc.)

### Phase 2: Data Exploration

- [ ] Exploration notebook attached to environment
- [ ] Notebook can read data from Lakehouse
- [ ] Data profiling complete

### Phase 3: Training

- [ ] Experiment created
- [ ] Training notebook runs successfully
- [ ] MLflow logging working
- [ ] Metrics tracked in experiment

### Phase 4: Model Registration

- [ ] Best run identified
- [ ] Model registered from experiment
- [ ] Model version tagged

### Phase 5: Batch Predictions

- [ ] Prediction notebook loads model successfully
- [ ] Predictions written to Lakehouse
- [ ] Prediction table accessible

### Phase 6: Visualization

- [ ] Report built on Lakehouse data
- [ ] Predictions visible in report
- [ ] Model metrics dashboard (optional)
