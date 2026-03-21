from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict

class TransactionRequest(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    timestamp: datetime = Field(default_factory=datetime.now)
    merchant_category: str
    location: str

class PredictionResponse(BaseModel):
    transaction_id: str
    risk_score: float
    is_fraud: bool
    explanation: Dict[str, float]
    decision: str
    timestamp: datetime
