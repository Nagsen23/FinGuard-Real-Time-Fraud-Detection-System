"""
src/ml/anomaly_detection.py
----------------------------
Production wrapper around sklearn IsolationForest.
Outputs are normalized to [0, 1] so they can be directly combined
with the supervised model's fraud probability in the risk engine.
"""

import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Unsupervised anomaly detector for catching novel / zero-day fraud patterns.

    Scoring is normalized:
      - 0.0 → perfectly normal
      - 1.0 → extremely anomalous

    Usage
    -----
    Training::

        detector = AnomalyDetector()
        detector.train(X_train)
        detector.save("models/anomaly_model.joblib")

    Inference::

        detector = AnomalyDetector.load("models/anomaly_model.joblib")
        scores   = detector.predict_anomaly_score(X_new)  # ndarray in [0,1]
    """

    def __init__(
        self,
        contamination: float = 0.035,
        n_estimators: int = 200,
        random_state: int = 42,
    ):
        self._contamination = contamination
        self._model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_features=1.0,
            random_state=random_state,
            n_jobs=-1,
        )
        self._is_trained = False

        # Fitted normalization bounds (set during train)
        self._score_min: float = 0.0
        self._score_max: float = 1.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def train(self, X: pd.DataFrame) -> "AnomalyDetector":
        """
        Fit the Isolation Forest on the full (unlabelled) training data.
        Also learns the min/max of decision_function scores for normalization.
        """
        logger.info("Training IsolationForest on %d samples…", len(X))
        self._model.fit(X.values)

        # Learn the score range for min-max normalization
        raw_scores = self._model.decision_function(X.values)
        self._score_min = float(raw_scores.min())
        self._score_max = float(raw_scores.max())
        self._is_trained = True
        logger.info("IsolationForest trained. Score range [%.4f, %.4f]",
                     self._score_min, self._score_max)
        return self

    def score_samples(self, X: pd.DataFrame) -> np.ndarray:
        """Return raw decision_function scores (lower = more anomalous)."""
        if not self._is_trained:
            raise RuntimeError("Detector not trained. Call train() or load() first.")
        return self._model.decision_function(X.values)

    def predict_anomaly_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Normalized anomaly score in [0, 1].
        Higher = more anomalous (intuitive for downstream risk scoring).

        Normalization:
          1. raw  = decision_function(X)   [lower = more anomalous]
          2. norm = (raw - min) / (max - min)   → [0, 1] with 1 = normal
          3. flip = 1 - norm                    → [0, 1] with 1 = anomalous
        """
        raw = self.score_samples(X)

        # Guard against zero-range edge case
        denom = self._score_max - self._score_min
        if denom == 0:
            return np.zeros(len(raw))

        normalized = (raw - self._score_min) / denom   # 0 = anomalous, 1 = normal
        flipped    = 1.0 - normalized                   # 0 = normal,    1 = anomalous
        return np.clip(flipped, 0.0, 1.0).astype(float)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("AnomalyDetector saved → %s", path)

    @classmethod
    def load(cls, path: str) -> "AnomalyDetector":
        obj = joblib.load(path)
        logger.info("AnomalyDetector loaded ← %s", path)
        return obj

    def __repr__(self) -> str:
        s = "trained" if self._is_trained else "untrained"
        return f"AnomalyDetector(contamination={self._contamination}, status={s})"
