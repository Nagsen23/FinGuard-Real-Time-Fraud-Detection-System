from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Literal
from enum import Enum


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Decision(str, Enum):
    allow = "ALLOW"
    review = "REVIEW"
    block = "BLOCK"


class TopReason(BaseModel):
    """A single feature contribution explaining the fraud decision."""
    feature: str = Field(..., description="Name of the contributing feature")
    contribution: float = Field(..., description="SHAP or importance weight (–1 to 1)")
    direction: Literal["increases_risk", "decreases_risk"] = Field(
        ..., description="Whether this feature pushes the score up or down"
    )


class PredictionResponse(BaseModel):
    """
    Full fraud detection prediction result.
    Includes probability, anomaly score, human-readable risk level,
    a final operational decision, and the top feature explanations.
    """

    transaction_id: str = Field(..., description="Echoed back from the request for traceability")

    # --- Scores ---
    fraud_probability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Supervised model's probability that this transaction is fraudulent"
    )
    anomaly_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Isolation Forest anomaly score (0 = normal, 1 = highly anomalous)"
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Human-readable risk tier derived from the combined risk score"
    )

    # --- Decision ---
    decision: Decision = Field(
        ...,
        description="Final operational action: ALLOW / REVIEW / BLOCK"
    )

    # --- Explainability ---
    top_reasons: List[TopReason] = Field(
        ...,
        description="Top 3–5 feature contributions explaining the prediction",
        max_length=5,
    )

    # --- Audit ---
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of when the prediction was generated"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "transaction_id": "tx_prod_demo_001",
                    "fraud_probability": 0.87,
                    "anomaly_score": 0.73,
                    "risk_level": "high",
                    "decision": "BLOCK",
                    "top_reasons": [
                        {"feature": "amount_log", "contribution": 0.45, "direction": "increases_risk"},
                        {"feature": "night_transaction", "contribution": 0.30, "direction": "increases_risk"},
                        {"feature": "is_international", "contribution": 0.20, "direction": "increases_risk"},
                    ],
                    "timestamp": "2026-03-20T14:00:00Z",
                }
            ]
        }
    }
