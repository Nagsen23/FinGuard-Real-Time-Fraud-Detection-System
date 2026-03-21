"""
tests/test_api.py
------------------
Schema validation tests for TransactionRequest and PredictionResponse.
Verifies:
  - Valid payloads parse without errors
  - Invalid/missing required fields raise ValidationError
  - Field validators (country uppercase, amount rounding) work correctly
  - Response schema fields and types are correct
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.api.schemas.request import TransactionRequest, TransactionType, MerchantCategory
from src.api.schemas.response import PredictionResponse, RiskLevel, Decision, TopReason


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_request_data() -> dict:
    return {
        "transaction_id": "tx_test_001",
        "user_id": "user_42",
        "merchant_id": "merchant_99",
        "amount": 120.995,
        "transaction_type": "purchase",
        "merchant_category": "retail",
        "device_type": "mobile",
        "channel": "mobile_app",
        "city": "London",
        "country": "gb",  # lowercase — should be normalized to "GB"
        "is_international": True,
        "card_present": False,
    }


@pytest.fixture
def valid_response_data() -> dict:
    return {
        "transaction_id": "tx_test_001",
        "fraud_probability": 0.85,
        "anomaly_score": 0.62,
        "risk_level": "high",
        "decision": "BLOCK",
        "top_reasons": [
            {"feature": "amount_log", "contribution": 0.45, "direction": "increases_risk"},
            {"feature": "is_international", "contribution": 0.30, "direction": "increases_risk"},
        ],
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# TransactionRequest Tests
# ---------------------------------------------------------------------------

class TestTransactionRequestSchema:

    def test_valid_payload_parses(self, valid_request_data):
        req = TransactionRequest(**valid_request_data)
        assert req.transaction_id == "tx_test_001"

    def test_country_uppercased(self, valid_request_data):
        req = TransactionRequest(**valid_request_data)
        assert req.country == "GB", "country should be coerced to uppercase"

    def test_amount_rounded(self, valid_request_data):
        req = TransactionRequest(**valid_request_data)
        assert req.amount == 121.00, "amount should be rounded to 2 decimal places"

    def test_missing_transaction_id_raises(self, valid_request_data):
        bad = {k: v for k, v in valid_request_data.items() if k != "transaction_id"}
        with pytest.raises(ValidationError):
            TransactionRequest(**bad)

    def test_missing_user_id_raises(self, valid_request_data):
        bad = {k: v for k, v in valid_request_data.items() if k != "user_id"}
        with pytest.raises(ValidationError):
            TransactionRequest(**bad)

    def test_negative_amount_raises(self, valid_request_data):
        bad = {**valid_request_data, "amount": -50.0}
        with pytest.raises(ValidationError):
            TransactionRequest(**bad)

    def test_zero_amount_raises(self, valid_request_data):
        bad = {**valid_request_data, "amount": 0}
        with pytest.raises(ValidationError):
            TransactionRequest(**bad)

    def test_invalid_transaction_type_raises(self, valid_request_data):
        bad = {**valid_request_data, "transaction_type": "gambling"}
        with pytest.raises(ValidationError):
            TransactionRequest(**bad)

    def test_invalid_merchant_category_raises(self, valid_request_data):
        bad = {**valid_request_data, "merchant_category": "rocket_fuel"}
        with pytest.raises(ValidationError):
            TransactionRequest(**bad)

    def test_default_device_type(self, valid_request_data):
        """device_type has a default of 'unknown' — should not raise if missing."""
        payload = {k: v for k, v in valid_request_data.items() if k != "device_type"}
        req = TransactionRequest(**payload)
        assert req.device_type.value == "unknown"

    def test_default_timestamp_set(self, valid_request_data):
        """Timestamp should default to now if not provided."""
        payload = {k: v for k, v in valid_request_data.items() if k != "timestamp"}
        req = TransactionRequest(**payload)
        assert isinstance(req.timestamp, datetime)

    def test_boolean_fields(self, valid_request_data):
        req = TransactionRequest(**valid_request_data)
        assert req.is_international is True
        assert req.card_present is False


# ---------------------------------------------------------------------------
# PredictionResponse Tests
# ---------------------------------------------------------------------------

class TestPredictionResponseSchema:

    def test_valid_response_parses(self, valid_response_data):
        resp = PredictionResponse(**valid_response_data)
        assert resp.decision == Decision.block

    def test_risk_level_enum(self, valid_response_data):
        resp = PredictionResponse(**valid_response_data)
        assert resp.risk_level == RiskLevel.high

    def test_fraud_probability_out_of_range_raises(self, valid_response_data):
        bad = {**valid_response_data, "fraud_probability": 1.5}
        with pytest.raises(ValidationError):
            PredictionResponse(**bad)

    def test_anomaly_score_out_of_range_raises(self, valid_response_data):
        bad = {**valid_response_data, "anomaly_score": -0.1}
        with pytest.raises(ValidationError):
            PredictionResponse(**bad)

    def test_top_reasons_structure(self, valid_response_data):
        resp = PredictionResponse(**valid_response_data)
        assert len(resp.top_reasons) == 2
        assert resp.top_reasons[0].feature == "amount_log"
        assert resp.top_reasons[0].direction == "increases_risk"

    def test_invalid_decision_raises(self, valid_response_data):
        bad = {**valid_response_data, "decision": "IGNORE"}
        with pytest.raises(ValidationError):
            PredictionResponse(**bad)
