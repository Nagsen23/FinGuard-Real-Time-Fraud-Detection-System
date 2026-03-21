from src.ml.feature_pipeline import FeaturePipeline
from src.ml.model_wrapper import SupervisedModel
from src.ml.anomaly_detection import AnomalyDetector
from datetime import datetime
import pandas as pd

def test_logic():
    print("Initializing components...")
    pipeline = FeaturePipeline()
    s_model = SupervisedModel()
    a_model = AnomalyDetector()
    
    data = {
        "transaction_id": "tx_12345",
        "user_id": "user_99",
        "amount": 5000.0,
        "timestamp": datetime.now().isoformat(),
        "merchant_category": "electronics",
        "location": "New York"
    }
    
    print(f"Transforming data: {data}")
    try:
        features = pipeline.transform(data)
        print(f"Features created: \n{features}")
        
        s_score = s_model.predict_proba(features)
        print(f"Supervised Score: {s_score}")
        
        a_score = a_model.predict_score(features)
        print(f"Anomaly Score: {a_score}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_logic()
