"""
src/ml/inference.py
--------------------
Orchestration layer for real-time fraud prediction.
Loads model artifacts and handles the end-to-end scoring flow.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from src.ml.feature_pipeline import FeaturePipeline
from src.ml.supervised_model import SupervisedModel
from src.ml.anomaly_detection import AnomalyDetector
from src.ml.risk_engine import RiskEngine, RiskResult
from src.ml.explainer_lite import get_top_reasons

logger = logging.getLogger(__name__)

# ── Global Paths ───────────────────────────────────────────────────────────
MODEL_DIR = Path("models")
PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.joblib"
SUPERVISED_PATH   = MODEL_DIR / "supervised_model.joblib"
ANOMALY_PATH      = MODEL_DIR / "anomaly_model.joblib"
METADATA_PATH     = MODEL_DIR / "metadata.json"


class FraudInference:
    """
    Singleton-style inference service.
    Loads models on initialization and provides a synchronous predict() method.
    """

    def __init__(self):
        self._initialized = False
        self.pipeline = None
        self.supervised_model = None
        self.anomaly_detector = None
        self.risk_engine = None
        self.metadata = None
        
        # Load artifacts
        try:
            self._load_artifacts()
            self.risk_engine = RiskEngine()  # Using default thresholds for now
            self._initialized = True
            logger.info("FraudInference service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize FraudInference: {e}")
            # We don't raise here to allow the API to start but return 503 later

    def _load_artifacts(self):
        """Loads all joblib artifacts and metadata."""
        if not METADATA_PATH.exists():
            raise FileNotFoundError(f"Metadata not found at {METADATA_PATH}")

        self.metadata = json.loads(METADATA_PATH.read_text())
        self.pipeline = FeaturePipeline.load(str(PREPROCESSOR_PATH))
        self.supervised_model = SupervisedModel.load(str(SUPERVISED_PATH))
        self.anomaly_detector = AnomalyDetector.load(str(ANOMALY_PATH))

    def predict(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full inference flow for a single transaction.
        
        Args:
            transaction: Raw transaction dictionary (matches TransactionRequest schema)
            
        Returns:
            Dictionary matching the PredictionResponse schema.
        """
        if not self._initialized:
            raise RuntimeError("Inference service is not initialized (models missing?)")

        # 1. Preprocess
        X = self.pipeline.transform(transaction)

        # 2. Model Scoring
        fraud_prob = float(self.supervised_model.predict_proba(X)[0])
        anomaly_score = float(self.anomaly_detector.predict_anomaly_score(X)[0])

        # 3. Risk Assessment
        risk_result: RiskResult = self.risk_engine.evaluate(
            fraud_probability=fraud_prob,
            anomaly_score=anomaly_score
        )

        # 4. Explainability (Lite)
        reasons = get_top_reasons(transaction, risk_result)

        # 5. Build Response
        return {
            "transaction_id": transaction.get("transaction_id", "unknown"),
            "fraud_probability": round(risk_result.fraud_probability, 4),
            "anomaly_score": round(risk_result.anomaly_score, 4),
            "risk_level": risk_result.risk_level,
            "decision": risk_result.decision,
            "top_reasons": reasons,
            "timestamp": datetime.now().isoformat()
        }

    @property
    def is_ready(self) -> bool:
        return self._initialized
