import joblib
import pandas as pd
from xgboost import XGBClassifier
from src.config import settings

class SupervisedModel:
    def __init__(self):
        self.model = None
        self.load_model()
        
    def load_model(self):
        try:
            self.model = joblib.load(settings.SUPERVISED_MODEL_PATH)
        except Exception as e:
            print(f"Supervised model not found at {settings.SUPERVISED_MODEL_PATH}")
            self.model = None
            
    def predict_proba(self, X: pd.DataFrame) -> float:
        if self.model:
            # Assumes binary classification, returns probability for class 1 (Fraud)
            return float(self.model.predict_proba(X)[0][1])
        return 0.0
