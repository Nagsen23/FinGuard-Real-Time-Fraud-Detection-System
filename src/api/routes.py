from fastapi import APIRouter, HTTPException
from src.api.schemas import TransactionRequest, PredictionResponse
from src.ml.feature_pipeline import FeaturePipeline
from src.ml.model_wrapper import SupervisedModel
from src.ml.anomaly_detection import AnomalyDetector
from src.ml.explainer import Explainer
from src.services.storage import StorageService
from src.config import settings
from datetime import datetime
import traceback

router = APIRouter()

# Initialize components
feature_pipeline = FeaturePipeline()
supervised_model = SupervisedModel()
anomaly_detector = AnomalyDetector()
explainer = Explainer(settings.SUPERVISED_MODEL_PATH)
storage = StorageService()

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: TransactionRequest):
    try:
        # 1. Feature Engineering (dict handles timestamp robustness internally)
        data = request.model_dump()
        features = feature_pipeline.transform(data)
        
        # 2. Hybrid Scoring
        s_score = supervised_model.predict_proba(features)
        a_score = anomaly_detector.predict_score(features)
        final_score = (settings.SUPERVISED_WEIGHT * s_score) + (settings.ANOMALY_WEIGHT * a_score)
        
        # 3. Decision
        decision = "BLOCK" if final_score > settings.THRESHOLD else "ALLOW"
        
        # 4. Explainability
        explanation = explainer.explain(features)
        
        # 5. Storage
        storage.store_transaction(
            request.transaction_id,
            request.user_id,
            request.amount,
            final_score,
            decision,
            explanation
        )
        
        return PredictionResponse(
            transaction_id=request.transaction_id,
            risk_score=final_score,
            is_fraud=decision == "BLOCK",
            explanation=explanation,
            decision=decision,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
