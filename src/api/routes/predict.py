"""
src/api/routes/predict.py
--------------------------
FastAPI route for real-time fraud prediction.
"""

from fastapi import APIRouter, HTTPException, Depends
from src.api.schemas.request import TransactionRequest
from src.api.schemas.response import PredictionResponse
from src.ml.inference import FraudInference
from src.services.audit_service import audit_service

router = APIRouter()

# Global instance of the inference service
_inference_service = FraudInference()

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: TransactionRequest):
    """
    Analyze a transaction for potential fraud and log the result.
    """
    if not _inference_service.is_ready:
        raise HTTPException(
            status_code=503, 
            detail="Inference service is currently unavailable (models not loaded)"
        )

    try:
        # Convert Pydantic model to dict for the inference layer
        transaction_data = request.model_dump()
        
        # Run inference
        result = _inference_service.predict(transaction_data)
        
        # --- Audit Logging ---
        audit_service.log_prediction(
            transaction_id=request.transaction_id,
            user_id=request.user_id,
            request_payload=transaction_data,
            prediction_result=result
        )
        
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred during fraud analysis"
        )

@router.get("/health/models")
async def model_health():
    """
    Check if models are correctly loaded.
    """
    return {
        "status": "ready" if _inference_service.is_ready else "not_ready",
        "metadata": _inference_service.metadata if _inference_service.is_ready else None
    }
