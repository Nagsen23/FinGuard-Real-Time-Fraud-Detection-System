import pandas as pd
import numpy as np
import joblib
import os
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from src.config import settings

def train_mocks():
    if not os.path.exists(settings.MODEL_DIR):
        os.makedirs(settings.MODEL_DIR)
        
    # Generate dummy data
    # Features: amount_log, hour, day_of_week
    X = pd.DataFrame({
        "amount_log": np.random.rand(100) * 10,
        "hour": np.random.randint(0, 24, 100),
        "day_of_week": np.random.randint(0, 7, 100)
    })
    y = np.random.randint(0, 2, 100)
    
    # 1. XGBoost
    supervised = XGBClassifier()
    supervised.fit(X, y)
    joblib.dump(supervised, settings.SUPERVISED_MODEL_PATH)
    print(f"Saved mock supervised model to {settings.SUPERVISED_MODEL_PATH}")
    
    # 2. Isolation Forest
    anomaly = IsolationForest(contamination=0.1)
    anomaly.fit(X)
    joblib.dump(anomaly, settings.ANOMALY_MODEL_PATH)
    print(f"Saved mock anomaly model to {settings.ANOMALY_MODEL_PATH}")

if __name__ == "__main__":
    train_mocks()
