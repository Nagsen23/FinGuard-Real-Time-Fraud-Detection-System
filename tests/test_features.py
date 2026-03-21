"""
tests/test_features.py
-----------------------
Unit tests for the FeaturePipeline, verifying:
  - Output shape (correct number of features)
  - Expected column order
  - Transformation of safe vs suspicious payloads
  - Graceful handling of missing optional fields
  - Unfitted pipeline raises RuntimeError
"""

import json
import pytest
import pandas as pd
from pathlib import Path

from src.ml.feature_pipeline import FeaturePipeline, FEATURE_COLUMNS

# ---------------------------------------------------------------------------
# Fixtures — load example payloads from the examples/ folder
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture
def safe_payload() -> dict:
    with open(ROOT / "examples" / "safe_transaction.json") as f:
        return json.load(f)


@pytest.fixture
def suspicious_payload() -> dict:
    with open(ROOT / "examples" / "suspicious_transaction.json") as f:
        return json.load(f)


@pytest.fixture
def fitted_pipeline(safe_payload, suspicious_payload) -> FeaturePipeline:
    """Return a pipeline fitted on both example payloads."""
    pipeline = FeaturePipeline()
    pipeline.fit([safe_payload, suspicious_payload])
    return pipeline


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFeaturePipelineBasic:
    def test_output_is_dataframe(self, fitted_pipeline, safe_payload):
        result = fitted_pipeline.transform(safe_payload)
        assert isinstance(result, pd.DataFrame)

    def test_output_column_count(self, fitted_pipeline, safe_payload):
        result = fitted_pipeline.transform(safe_payload)
        assert result.shape[1] == len(FEATURE_COLUMNS), (
            f"Expected {len(FEATURE_COLUMNS)} features, got {result.shape[1]}"
        )

    def test_output_column_order(self, fitted_pipeline, safe_payload):
        result = fitted_pipeline.transform(safe_payload)
        assert list(result.columns) == FEATURE_COLUMNS

    def test_output_is_all_numeric(self, fitted_pipeline, safe_payload):
        result = fitted_pipeline.transform(safe_payload)
        assert result.dtypes.apply(lambda d: pd.api.types.is_float_dtype(d)).all(), (
            "All output columns must be float"
        )

    def test_single_row_output(self, fitted_pipeline, safe_payload):
        result = fitted_pipeline.transform(safe_payload)
        assert result.shape[0] == 1

    def test_batch_transform(self, fitted_pipeline, safe_payload, suspicious_payload):
        result = fitted_pipeline.transform([safe_payload, suspicious_payload])
        assert result.shape[0] == 2


class TestTemporalFeatures:
    def test_night_transaction_flagged(self, fitted_pipeline, suspicious_payload):
        """Suspicious payload has timestamp at 02:55, which is a night transaction."""
        result = fitted_pipeline.transform(suspicious_payload)
        # The "is_night_transaction" column — find its index
        idx = FEATURE_COLUMNS.index("is_night_transaction")
        raw_pipeline = FeaturePipeline()
        # Quick check using _base_transform (no scaling distortion)
        df = raw_pipeline._base_transform([suspicious_payload])
        assert df["is_night_transaction"].iloc[0] == 1, "02:55 should be a night transaction"

    def test_day_transaction_not_flagged(self, fitted_pipeline, safe_payload):
        """Safe payload has timestamp at 10:30, which is not a night transaction."""
        raw_pipeline = FeaturePipeline()
        df = raw_pipeline._base_transform([safe_payload])
        assert df["is_night_transaction"].iloc[0] == 0, "10:30 should NOT be a night transaction"

    def test_hour_extraction(self, fitted_pipeline, safe_payload):
        raw_pipeline = FeaturePipeline()
        df = raw_pipeline._base_transform([safe_payload])
        assert df["hour"].iloc[0] == 10


class TestAmountFeatures:
    def test_log_amount_is_positive(self, fitted_pipeline, safe_payload):
        raw_pipeline = FeaturePipeline()
        df = raw_pipeline._base_transform([safe_payload])
        assert df["amount_log"].iloc[0] > 0

    def test_zero_amount_handled(self, fitted_pipeline, safe_payload):
        """amount=0 should not cause log errors."""
        broken = {**safe_payload, "amount": 0}
        raw_pipeline = FeaturePipeline()
        df = raw_pipeline._base_transform([broken])
        assert df["amount_log"].iloc[0] == pytest.approx(0.0)


class TestBooleanNormalization:
    def test_is_international_int(self, fitted_pipeline, suspicious_payload):
        raw_pipeline = FeaturePipeline()
        df = raw_pipeline._base_transform([suspicious_payload])
        assert df["is_international"].iloc[0] == 1

    def test_card_not_present_int(self, fitted_pipeline, suspicious_payload):
        raw_pipeline = FeaturePipeline()
        df = raw_pipeline._base_transform([suspicious_payload])
        assert df["card_present"].iloc[0] == 0


class TestPipelineErrors:
    def test_transform_without_fit_raises(self, safe_payload):
        pipeline = FeaturePipeline()
        with pytest.raises(RuntimeError, match="not been fitted"):
            pipeline.transform(safe_payload)

    def test_fit_transform_is_consistent(self, safe_payload, suspicious_payload):
        """fit_transform should produce same result as fit + transform."""
        p1 = FeaturePipeline()
        result_ft = p1.fit_transform([safe_payload, suspicious_payload])

        p2 = FeaturePipeline()
        p2.fit([safe_payload, suspicious_payload])
        result_t = p2.transform([safe_payload, suspicious_payload])

        pd.testing.assert_frame_equal(result_ft, result_t)

    def test_missing_optional_field_handled(self, fitted_pipeline, safe_payload):
        """A payload missing 'device_type' should fall back to 'unknown', not raise."""
        incomplete = {k: v for k, v in safe_payload.items() if k != "device_type"}
        result = fitted_pipeline.transform(incomplete)
        assert result.shape[1] == len(FEATURE_COLUMNS)
