"""
src/ml/supervised_model.py
---------------------------
Production wrapper around a supervised classifier (XGBoost preferred, RandomForest fallback).
Exposes a clean train / predict_proba / save / load interface.
"""

import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Model selection: XGBoost if available, else sklearn RandomForest ────────
try:
    from xgboost import XGBClassifier
    _DEFAULT_ALGO = "XGBClassifier"
except ImportError:
    from sklearn.ensemble import RandomForestClassifier as XGBClassifier  # noqa: N811
    _DEFAULT_ALGO = "RandomForestClassifier"
    logger.info("XGBoost not installed — falling back to RandomForestClassifier.")


class SupervisedModel:
    """
    Binary fraud classifier.

    Usage
    -----
    Training::

        model = SupervisedModel()
        model.train(X_train, y_train)
        model.save("models/supervised_model.joblib")

    Inference::

        model = SupervisedModel.load("models/supervised_model.joblib")
        probs = model.predict_proba(X_new)   # ndarray of shape (n,)
    """

    def __init__(self, random_state: int = 42):
        self._random_state = random_state
        self._model = self._build_model()
        self._is_trained = False
        self.algorithm = _DEFAULT_ALGO

    # ------------------------------------------------------------------
    # Internal: build the underlying sklearn/XGB estimator
    # ------------------------------------------------------------------
    def _build_model(self):
        if _DEFAULT_ALGO == "XGBClassifier":
            return XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=10,       # handle class imbalance (~3.5% fraud)
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=self._random_state,
                n_jobs=-1,
            )
        else:
            return XGBClassifier(              # actually RandomForest (aliased)
                n_estimators=300,
                max_depth=12,
                class_weight="balanced",       # handle imbalance
                random_state=self._random_state,
                n_jobs=-1,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def train(self, X: pd.DataFrame, y: pd.Series) -> "SupervisedModel":
        """Train on labelled feature matrix."""
        logger.info("Training %s on %d samples, %d features…",
                     self.algorithm, len(X), X.shape[1])
        self._model.fit(X.values, y.values)
        self._is_trained = True
        logger.info("Training complete.")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return P(fraud) for each row — a 1-D array of floats in [0, 1].
        """
        if not self._is_trained:
            raise RuntimeError("Model has not been trained. Call train() or load() first.")
        probs = self._model.predict_proba(X.values)
        # Column 1 = probability of the positive class (fraud)
        return probs[:, 1].astype(float)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("SupervisedModel saved → %s", path)

    @classmethod
    def load(cls, path: str) -> "SupervisedModel":
        obj = joblib.load(path)
        logger.info("SupervisedModel loaded ← %s", path)
        return obj

    def __repr__(self) -> str:
        s = "trained" if self._is_trained else "untrained"
        return f"SupervisedModel(algo={self.algorithm}, status={s})"
