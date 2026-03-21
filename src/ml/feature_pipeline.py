"""
src/ml/feature_pipeline.py
---------------------------
Reusable preprocessing pipeline for both training and real-time inference.
Exposes a sklearn-compatible FeaturePipeline class with fit(), transform(), and fit_transform() methods.

Design Principles:
- Training and inference use the EXACT same code path to prevent training-serving skew.
- All state (encoders, scaler parameters) is serialized via joblib for reproducibility.
- All input validation is handled upstream at the API schema layer; this module assumes clean dicts.
"""

import pandas as pd
import numpy as np
import joblib
import logging
from datetime import datetime
from typing import Any, List, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature Constants
# ---------------------------------------------------------------------------

# Categorical columns that will be label-encoded
CATEGORICAL_COLS = [
    "transaction_type",
    "merchant_category",
    "device_type",
    "channel",
    "country",
]

# Numeric columns that will be scaled
NUMERIC_COLS = [
    "amount",
    "amount_log",
    "hour",
    "day_of_week",
]

# Boolean columns — already {0, 1}, no encoding needed
BOOLEAN_COLS = [
    "is_international",
    "card_present",
    "is_weekend",
    "is_night_transaction",
]

# Final ordered feature list output by transform()
FEATURE_COLUMNS: List[str] = (
    ["amount_log"]
    + CATEGORICAL_COLS
    + ["hour", "day_of_week", "is_weekend", "is_night_transaction"]
    + ["is_international", "card_present"]
)


# ---------------------------------------------------------------------------
# Helper: Raw dict → Base DataFrame
# ---------------------------------------------------------------------------

def _raw_to_df(data: dict | list[dict]) -> pd.DataFrame:
    """Convert a single transaction dict or list of dicts to a DataFrame."""
    if isinstance(data, dict):
        return pd.DataFrame([data])
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Helper: Timestamp Feature Extraction
# ---------------------------------------------------------------------------

def _extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive time-based risk signals from the timestamp column.
    - hour          (0-23)
    - day_of_week   (0=Mon, 6=Sun)
    - is_weekend    (Sat/Sun → 1)
    - is_night_transaction  (22:00–05:59 → 1, high-risk window)
    """
    ts_col = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

    df["hour"] = ts_col.dt.hour.fillna(0).astype(int)
    df["day_of_week"] = ts_col.dt.dayofweek.fillna(0).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_night_transaction"] = df["hour"].apply(
        lambda h: 1 if (h >= 22 or h < 6) else 0
    )
    return df


# ---------------------------------------------------------------------------
# Helper: Boolean Normalization
# ---------------------------------------------------------------------------

def _normalize_booleans(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure bool/nullable-bool columns are cast to int {0, 1}.
    Handles Python bools, strings ('True'/'False'), None → 0.
    """
    bool_map = {True: 1, False: 0, "true": 1, "false": 0, None: 0}
    for col in ["is_international", "card_present"]:
        if col in df.columns:
            df[col] = df[col].map(lambda v: bool_map.get(v, int(bool(v))))
    return df


# ---------------------------------------------------------------------------
# Core Pipeline Class
# ---------------------------------------------------------------------------

class FeaturePipeline:
    """
    Production feature pipeline for the fraud detection system.

    Usage
    -----
    Training:
        pipeline = FeaturePipeline()
        X_train = pipeline.fit_transform(training_data_list)
        pipeline.save("models/preprocessor.joblib")

    Inference:
        pipeline = FeaturePipeline.load("models/preprocessor.joblib")
        X = pipeline.transform(single_transaction_dict)
    """

    def __init__(self):
        self._label_encoders: dict[str, LabelEncoder] = {}
        self._scaler: Optional[StandardScaler] = None
        self._is_fitted: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, data: list[dict]) -> "FeaturePipeline":
        """
        Learn encoding and scaling parameters from a training dataset.
        Must be called before transform() during inference.
        """
        df = self._base_transform(data)

        # Fit categorical encoders
        for col in CATEGORICAL_COLS:
            le = LabelEncoder()
            df[col] = df[col].fillna("unknown").astype(str)
            le.fit(df[col])
            self._label_encoders[col] = le

        # Fit scaler on numeric features only
        numeric_data = df[["amount_log", "hour", "day_of_week"]].values
        self._scaler = StandardScaler()
        self._scaler.fit(numeric_data)

        self._is_fitted = True
        logger.info("FeaturePipeline fitted on %d samples.", len(data))
        return self

    def transform(self, data: dict | list[dict]) -> pd.DataFrame:
        """
        Transform one or more raw transaction dicts into a model-ready feature matrix.
        Requires the pipeline to have been fit() first.
        """
        if not self._is_fitted:
            raise RuntimeError(
                "Pipeline has not been fitted. Call fit() or load() before transform()."
            )

        if isinstance(data, dict):
            data = [data]

        df = self._base_transform(data)
        df = self._encode_categoricals(df)
        df = self._scale_numerics(df)

        return df[FEATURE_COLUMNS].astype(float)

    def fit_transform(self, data: list[dict]) -> pd.DataFrame:
        """Convenience method: fit then transform in one pass (for training)."""
        self.fit(data)
        return self.transform(data)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Serialize the fitted pipeline to disk."""
        joblib.dump(self, path)
        logger.info("FeaturePipeline saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "FeaturePipeline":
        """Deserialize a fitted pipeline from disk."""
        pipeline = joblib.load(path)
        logger.info("FeaturePipeline loaded from %s", path)
        return pipeline

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _base_transform(self, data: list[dict]) -> pd.DataFrame:
        """
        Step 1: Convert raw dicts to a DataFrame and apply deterministic transforms
        that require no fitted state (temporal extraction, boolean normalization, log amount).
        """
        df = _raw_to_df(data)

        # Handle missing values with safe defaults
        df["amount"] = pd.to_numeric(df.get("amount", 0), errors="coerce").fillna(0.0)
        df["amount"] = df["amount"].clip(lower=0)

        # Log-transform amount to reduce skewness
        df["amount_log"] = np.log1p(df["amount"])

        # Temporal features from timestamp
        if "timestamp" in df.columns:
            df = _extract_temporal_features(df)
        else:
            df["hour"] = datetime.now().hour
            df["day_of_week"] = datetime.now().weekday()
            df["is_weekend"] = int(datetime.now().weekday() >= 5)
            df["is_night_transaction"] = int(datetime.now().hour >= 22 or datetime.now().hour < 6)

        # Normalize booleans
        df = _normalize_booleans(df)

        # Fill missing categoricals with a safe sentinel
        for col in CATEGORICAL_COLS:
            if col not in df.columns:
                df[col] = "unknown"
            else:
                df[col] = df[col].fillna("unknown").astype(str)

        return df

    def _encode_categoricals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Label-encode each categorical column using the fitted encoders."""
        for col in CATEGORICAL_COLS:
            le = self._label_encoders[col]
            # Handle unseen categories gracefully (map to -1)
            known_classes = set(le.classes_)
            df[col] = df[col].apply(
                lambda v: le.transform([v])[0] if v in known_classes else -1
            )
        return df

    def _scale_numerics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standard-scale the numeric features using the fitted scaler."""
        numeric_cols = ["amount_log", "hour", "day_of_week"]
        df[numeric_cols] = self._scaler.transform(df[numeric_cols].values)
        return df

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_feature_names(self) -> List[str]:
        """Return the ordered list of output feature column names."""
        return FEATURE_COLUMNS

    def __repr__(self) -> str:
        status = "fitted" if self._is_fitted else "unfitted"
        return f"FeaturePipeline(status={status}, features={len(FEATURE_COLUMNS)})"
