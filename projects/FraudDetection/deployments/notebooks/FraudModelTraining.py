# FraudModelTraining Notebook
# Credit Card Fraud Detection - ML Model Training
# 
# Environment: FraudMLEnvironment (scikit-learn, xgboost, mlflow, pandas)
# Lakehouse: FraudLakehouse

# %% [markdown]
# # Credit Card Fraud Detection Model
# 
# This notebook trains and registers a fraud detection model using MLflow.

# %%
# Import libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
from xgboost import XGBClassifier
import mlflow
import mlflow.sklearn

# %%
# Configuration
EXPERIMENT_NAME = "FraudExperiment"
MODEL_NAME = "FraudDetectionModel"
FRAUD_THRESHOLD = 0.85

# Set MLflow experiment
mlflow.set_experiment(EXPERIMENT_NAME)

# %%
# Load training data from Lakehouse
# Historical transactions with known fraud labels
df = spark.read.format("delta").load("abfss://FraudLakehouse@onelake.dfs.fabric.microsoft.com/Tables/training_transactions").toPandas()

print(f"Loaded {len(df)} transactions")
print(f"Fraud rate: {df['is_fraud'].mean():.2%}")

# %%
# Feature engineering
features = ['amount', 'merchant_category', 'hour_of_day', 'day_of_week', 
            'distance_from_home', 'transaction_velocity', 'avg_transaction_amount']

X = df[features]
y = df['is_fraud']

# Handle categorical features
X = pd.get_dummies(X, columns=['merchant_category'])

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Training set: {len(X_train)} samples")
print(f"Test set: {len(X_test)} samples")

# %%
# Train XGBoost model with MLflow tracking
with mlflow.start_run(run_name="xgboost_fraud_detection") as run:
    # Model parameters
    params = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'scale_pos_weight': len(y_train[y_train==0]) / len(y_train[y_train==1]),  # Handle imbalance
        'random_state': 42
    }
    
    # Log parameters
    mlflow.log_params(params)
    
    # Train model
    model = XGBClassifier(**params)
    model.fit(X_train_scaled, y_train)
    
    # Predictions
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate metrics
    auc_score = roc_auc_score(y_test, y_pred_proba)
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
    
    # Log metrics
    mlflow.log_metric("auc_score", auc_score)
    mlflow.log_metric("precision_at_threshold", precision[np.searchsorted(thresholds, FRAUD_THRESHOLD)])
    mlflow.log_metric("recall_at_threshold", recall[np.searchsorted(thresholds, FRAUD_THRESHOLD)])
    
    # Log model
    mlflow.sklearn.log_model(model, "fraud_model")
    
    # Register model
    model_uri = f"runs:/{run.info.run_id}/fraud_model"
    mlflow.register_model(model_uri, MODEL_NAME)
    
    print(f"Run ID: {run.info.run_id}")
    print(f"AUC Score: {auc_score:.4f}")
    print(f"\nClassification Report:\n{classification_report(y_test, (y_pred_proba > FRAUD_THRESHOLD).astype(int))}")

# %%
# Save scaler for inference
import joblib
joblib.dump(scaler, "/lakehouse/default/Files/models/scaler.pkl")

# %%
# Scoring function for real-time inference
def score_transaction(transaction_data: dict) -> float:
    """
    Score a single transaction for fraud probability.
    
    Args:
        transaction_data: Dict with transaction features
        
    Returns:
        Fraud probability score (0.0 - 1.0)
    """
    # Load model from registry
    model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}/latest")
    scaler = joblib.load("/lakehouse/default/Files/models/scaler.pkl")
    
    # Prepare features
    features_df = pd.DataFrame([transaction_data])
    features_scaled = scaler.transform(features_df)
    
    # Predict
    fraud_score = model.predict_proba(features_scaled)[0, 1]
    
    return float(fraud_score)

# %%
# Test scoring function
test_transaction = {
    'amount': 5000.00,
    'hour_of_day': 2,
    'day_of_week': 6,
    'distance_from_home': 500,
    'transaction_velocity': 5,
    'avg_transaction_amount': 100
}

fraud_score = score_transaction(test_transaction)
print(f"Fraud score: {fraud_score:.4f}")
print(f"Alert triggered: {fraud_score > FRAUD_THRESHOLD}")
