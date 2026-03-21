"""
tests/test_inference.py
------------------------
Tests for the full ML training + scoring pipeline:
  - Training completes without error
  - Artifacts are saved to disk
  - Supervised model returns valid probabilities
  - Anomaly model returns normalized scores in [0, 1]
  - Risk engine returns valid RiskResult structure
  - End-to-end: raw dict → risk decision
"""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.ml.feature_pipeline import FeaturePipeline, FEATURE_COLUMNS
from src.ml.supervised_model import SupervisedModel
from src.ml.anomaly_detection import AnomalyDetector
from src.ml.risk_engine import RiskEngine, RiskResult, RiskThresholds
from src.ml.train import run_training, MODEL_DIR, METADATA_PATH

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fixtures — tiny training set from 500 rows of the real data
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sample_data():
    """Load a small sample from the generated CSV for fast tests."""
    for name in ["transactions_v2.csv", "transactions.csv"]:
        p = ROOT / "data" / "raw" / name
        if p.exists():
            df = pd.read_csv(p).sample(n=500, random_state=42)
            return df.to_dict("records"), df["is_fraud"].values
    pytest.skip("No dataset found — run generate_dataset.py first.")


@pytest.fixture(scope="module")
def fitted_pipeline(sample_data):
    records, _ = sample_data
    pipeline = FeaturePipeline()
    X = pipeline.fit_transform(records)
    return pipeline, X


@pytest.fixture(scope="module")
def trained_supervised(fitted_pipeline, sample_data):
    _, y = sample_data
    pipeline, X = fitted_pipeline
    model = SupervisedModel()
    model.train(X, pd.Series(y))
    return model


@pytest.fixture(scope="module")
def trained_anomaly(fitted_pipeline):
    _, X = fitted_pipeline
    detector = AnomalyDetector()
    detector.train(X)
    return detector


# ---------------------------------------------------------------------------
# Supervised Model Tests
# ---------------------------------------------------------------------------

class TestSupervisedModel:

    def test_returns_1d_array(self, trained_supervised, fitted_pipeline):
        _, X = fitted_pipeline
        probs = trained_supervised.predict_proba(X)
        assert probs.ndim == 1
        assert len(probs) == len(X)

    def test_probabilities_in_range(self, trained_supervised, fitted_pipeline):
        _, X = fitted_pipeline
        probs = trained_supervised.predict_proba(X)
        assert probs.min() >= 0.0
        assert probs.max() <= 1.0

    def test_untrained_model_raises(self, fitted_pipeline):
        _, X = fitted_pipeline
        model = SupervisedModel()
        with pytest.raises(RuntimeError, match="not been trained"):
            model.predict_proba(X)

    def test_save_and_load(self, trained_supervised, fitted_pipeline, tmp_path):
        _, X = fitted_pipeline
        path = str(tmp_path / "test_sup.joblib")
        trained_supervised.save(path)
        loaded = SupervisedModel.load(path)
        np.testing.assert_array_almost_equal(
            trained_supervised.predict_proba(X),
            loaded.predict_proba(X),
        )


# ---------------------------------------------------------------------------
# Anomaly Detector Tests
# ---------------------------------------------------------------------------

class TestAnomalyDetector:

    def test_scores_in_0_1(self, trained_anomaly, fitted_pipeline):
        _, X = fitted_pipeline
        scores = trained_anomaly.predict_anomaly_score(X)
        assert scores.min() >= 0.0
        assert scores.max() <= 1.0

    def test_scores_1d(self, trained_anomaly, fitted_pipeline):
        _, X = fitted_pipeline
        scores = trained_anomaly.predict_anomaly_score(X)
        assert scores.ndim == 1
        assert len(scores) == len(X)

    def test_untrained_raises(self, fitted_pipeline):
        _, X = fitted_pipeline
        d = AnomalyDetector()
        with pytest.raises(RuntimeError, match="not trained"):
            d.predict_anomaly_score(X)

    def test_save_and_load(self, trained_anomaly, fitted_pipeline, tmp_path):
        _, X = fitted_pipeline
        path = str(tmp_path / "test_anom.joblib")
        trained_anomaly.save(path)
        loaded = AnomalyDetector.load(path)
        np.testing.assert_array_almost_equal(
            trained_anomaly.predict_anomaly_score(X),
            loaded.predict_anomaly_score(X),
        )


# ---------------------------------------------------------------------------
# Risk Engine Tests
# ---------------------------------------------------------------------------

class TestRiskEngine:

    def test_allow_decision(self):
        engine = RiskEngine()
        result = engine.evaluate(fraud_probability=0.05, anomaly_score=0.10)
        assert result.decision == "ALLOW"
        assert result.risk_level == "low"

    def test_review_decision(self):
        engine = RiskEngine()
        result = engine.evaluate(fraud_probability=0.50, anomaly_score=0.40)
        assert result.decision == "REVIEW"
        assert result.risk_level == "medium"

    def test_block_decision(self):
        engine = RiskEngine()
        result = engine.evaluate(fraud_probability=0.90, anomaly_score=0.80)
        assert result.decision == "BLOCK"
        assert result.risk_level in ("high", "critical")

    def test_result_structure(self):
        engine = RiskEngine()
        result = engine.evaluate(0.5, 0.5)
        assert isinstance(result, RiskResult)
        assert 0.0 <= result.combined_score <= 1.0

    def test_custom_thresholds(self):
        t = RiskThresholds(low_max=0.10, medium_max=0.30, high_max=0.60,
                           alpha=0.5, beta=0.5)
        engine = RiskEngine(thresholds=t)
        result = engine.evaluate(0.3, 0.3)
        assert result.combined_score == pytest.approx(0.3)
        assert result.risk_level == "medium"


# ---------------------------------------------------------------------------
# Full Training Pipeline Test
# ---------------------------------------------------------------------------

class TestTrainingPipeline:

    def test_run_training_completes(self):
        """Full pipeline should run without error."""
        metadata = run_training()
        assert isinstance(metadata, dict)

    def test_artifacts_exist(self):
        """All expected artifacts are saved to models/."""
        assert (MODEL_DIR / "supervised_model.joblib").exists()
        assert (MODEL_DIR / "anomaly_model.joblib").exists()
        assert (MODEL_DIR / "preprocessor.joblib").exists()
        assert METADATA_PATH.exists()

    def test_metadata_structure(self):
        """metadata.json has all expected keys."""
        raw = METADATA_PATH.read_text()
        meta = json.loads(raw)
        for key in ("model_version", "training_timestamp", "dataset_path",
                     "feature_names", "categorical_columns", "numeric_columns",
                     "thresholds", "algorithms", "metrics", "artifacts"):
            assert key in meta, f"Missing key: {key}"

    def test_loaded_models_produce_output(self):
        """Load saved artifacts and verify they produce valid output."""
        pipeline = FeaturePipeline.load(str(MODEL_DIR / "preprocessor.joblib"))
        sup      = SupervisedModel.load(str(MODEL_DIR / "supervised_model.joblib"))
        anom     = AnomalyDetector.load(str(MODEL_DIR / "anomaly_model.joblib"))

        sample = {
            "transaction_id": "tx_test_99",
            "user_id": "user_00001",
            "amount": 8500.0,
            "transaction_type": "transfer",
            "merchant_category": "other",
            "merchant_id": "mrc_othe_0001",
            "device_type": "unknown",
            "channel": "online",
            "city": "Offshore City",
            "country": "CY",
            "timestamp": "2026-03-20T03:00:00Z",
            "is_international": True,
            "card_present": False,
        }
        X = pipeline.transform(sample)
        assert X.shape == (1, len(FEATURE_COLUMNS))

        probs   = sup.predict_proba(X)
        assert 0.0 <= probs[0] <= 1.0

        a_score = anom.predict_anomaly_score(X)
        assert 0.0 <= a_score[0] <= 1.0
