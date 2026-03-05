#!/bin/bash
# fraud-detection-deploy.sh
# Credit Card Fraud Detection - Lambda Architecture Deployment
# Usage: ./fraud-detection-deploy.sh
# Prerequisites: fab auth login

set -e

WS="FraudDetection"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Credit Card Fraud Detection - Deployment Script              ║"
echo "║   Task flow: Lambda (Real-Time Focus)                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verify authentication
echo "🔐 Verifying authentication..."
fab auth show || { echo "❌ Not authenticated. Run: fab auth login"; exit 1; }

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 1: FOUNDATION (Storage)"
echo "═══════════════════════════════════════════════════════════════════"

echo "📦 Creating Eventhouse: FraudEventhouse..."
fab mkdir $WS.Workspace/FraudEventhouse.Eventhouse
EVENTHOUSE_ID=$(fab get $WS.Workspace/FraudEventhouse.Eventhouse -q id -o tsv)
echo "   ✅ Eventhouse created (ID: $EVENTHOUSE_ID)"

echo "📦 Creating KQL Database: FraudTransactions..."
fab mkdir $WS.Workspace/FraudTransactions.KQLDatabase -P eventhouseId=$EVENTHOUSE_ID
echo "   ✅ KQL Database created"

echo "📦 Creating Lakehouse: FraudLakehouse..."
fab mkdir $WS.Workspace/FraudLakehouse.Lakehouse
LAKEHOUSE_ID=$(fab get $WS.Workspace/FraudLakehouse.Lakehouse -q id -o tsv)
echo "   ✅ Lakehouse created (ID: $LAKEHOUSE_ID)"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 2: COMPUTE ENVIRONMENT"
echo "═══════════════════════════════════════════════════════════════════"

echo "📦 Creating Environment: FraudMLEnvironment..."
fab mkdir $WS.Workspace/FraudMLEnvironment.Environment
ENV_ID=$(fab get $WS.Workspace/FraudMLEnvironment.Environment -q id -o tsv)
echo "   ✅ Environment created (ID: $ENV_ID)"
echo ""
echo "   ⚠️  MANUAL ACTION REQUIRED:"
echo "   1. Open FraudMLEnvironment in portal"
echo "   2. Add libraries: scikit-learn, xgboost, mlflow, pandas"
echo "   3. Click 'Publish' (takes 10+ minutes)"
echo ""

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 3: INGESTION"
echo "═══════════════════════════════════════════════════════════════════"

echo "📦 Creating Eventstream: TransactionStream..."
fab mkdir $WS.Workspace/TransactionStream.Eventstream
echo "   ✅ Eventstream created"
echo ""
echo "   ⚠️  MANUAL ACTION REQUIRED:"
echo "   1. Configure Event Hub source connection"
echo "   2. Add ML scoring transformation node"
echo "   3. Set destination to FraudEventhouse"
echo ""

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 4: TRANSFORMATION (ML & Processing)"
echo "═══════════════════════════════════════════════════════════════════"

echo "📦 Creating Notebook: FraudModelTraining..."
fab mkdir $WS.Workspace/FraudModelTraining.Notebook
echo "   ✅ Notebook created"

echo "⚙️  Binding notebook to FraudLakehouse..."
fab set $WS.Workspace/FraudModelTraining.Notebook -q lakehouse -i "{\"id\": \"$LAKEHOUSE_ID\", \"displayName\": \"FraudLakehouse\"}"
echo "   ✅ Lakehouse bound"

echo "⚙️  Attaching environment to notebook..."
fab set $WS.Workspace/FraudModelTraining.Notebook -q environment -i "{\"id\": \"$ENV_ID\", \"displayName\": \"FraudMLEnvironment\"}"
echo "   ✅ Environment attached"

echo "📦 Creating Experiment: FraudExperiment..."
fab mkdir $WS.Workspace/FraudExperiment.MLExperiment
echo "   ✅ Experiment created"

echo "📦 Creating ML Model: FraudDetectionModel..."
fab mkdir $WS.Workspace/FraudDetectionModel.MLModel
echo "   ✅ ML Model created"

echo "📦 Creating KQL Queryset: FraudPatternQueries..."
fab mkdir $WS.Workspace/FraudPatternQueries.KQLQueryset
echo "   ✅ KQL Queryset created"
echo ""
echo "   ⚠️  MANUAL ACTION REQUIRED:"
echo "   Add fraud detection queries to FraudPatternQueries"
echo ""

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 5: MONITORING & ALERTING"
echo "═══════════════════════════════════════════════════════════════════"

echo "📦 Creating Activator: FraudAlerts..."
fab mkdir $WS.Workspace/FraudAlerts.Activator
echo "   ✅ Activator created"
echo ""
echo "   ⚠️  MANUAL ACTION REQUIRED:"
echo "   1. Configure trigger: fraud_score > 0.85"
echo "   2. Set up Email/Teams notification"
echo "   3. Enable the Activator"
echo ""

echo "📦 Creating Real-Time Dashboard: FraudMonitoringDashboard..."
fab mkdir $WS.Workspace/FraudMonitoringDashboard.RealtimeDashboard
echo "   ✅ Real-Time Dashboard created"
echo ""
echo "   ⚠️  MANUAL ACTION REQUIRED:"
echo "   1. Add tiles: Transaction Volume, Fraud Rate, Top Risk Merchants, Fraud Score Distribution"
echo "   2. Configure 30-second auto-refresh"
echo ""

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "VERIFICATION"
echo "═══════════════════════════════════════════════════════════════════"

echo "🔍 Verifying all items exist..."
ITEMS="FraudEventhouse.Eventhouse FraudLakehouse.Lakehouse FraudMLEnvironment.Environment TransactionStream.Eventstream FraudModelTraining.Notebook FraudExperiment.MLExperiment FraudDetectionModel.MLModel FraudPatternQueries.KQLQueryset FraudAlerts.Activator FraudMonitoringDashboard.RealtimeDashboard"

ALL_EXIST=true
for ITEM in $ITEMS; do
    if fab exists $WS.Workspace/$ITEM > /dev/null 2>&1; then
        echo "   ✅ $ITEM"
    else
        echo "   ❌ $ITEM NOT FOUND"
        ALL_EXIST=false
    fi
done

echo ""
echo "📋 Workspace contents:"
fab ls $WS.Workspace -l

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   DEPLOYMENT COMPLETE                                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Manual Steps Pending:"
echo "   1. Publish FraudMLEnvironment with libraries"
echo "   2. Configure TransactionStream (Event Hub → Eventhouse)"
echo "   3. Add KQL queries to FraudPatternQueries"
echo "   4. Configure FraudAlerts trigger (fraud_score > 0.85)"
echo "   5. Add dashboard tiles with 30s refresh"
echo ""
echo "🧪 Ready for validation: validation/lambda.md"
