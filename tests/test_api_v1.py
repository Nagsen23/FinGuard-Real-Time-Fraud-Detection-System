import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """Verify that the health check endpoint is reachable."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_predict_success_fraud():
    """Verify that a suspicious transaction returns a high fraud probability."""
    payload = {
        "transaction_id": "api_test_fraud_001",
        "user_id": "user_123",
        "amount": 25000.0,
        "merchant_id": "mrc_99",
        "transaction_type": "transfer",
        "merchant_category": "travel",
        "device_type": "unknown",
        "channel": "online",
        "city": "Unknown",
        "country": "US",
        "is_international": True,
        "card_present": False,
        "timestamp": "2026-03-20T02:30:00"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "api_test_fraud_001"
    assert data["fraud_probability"] > 0.5
    assert data["decision"] == "BLOCK"
    assert "top_reasons" in data
    assert len(data["top_reasons"]) > 0

def test_predict_success_safe():
    """Verify that a normal transaction returns a low fraud probability."""
    payload = {
        "transaction_id": "api_test_safe_001",
        "user_id": "user_456",
        "amount": 50.0,
        "merchant_id": "mrc_01",
        "transaction_type": "purchase",
        "merchant_category": "grocery",
        "device_type": "mobile",
        "channel": "mobile_app",
        "city": "London",
        "country": "GB",
        "is_international": False,
        "card_present": True
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["fraud_probability"] < 0.2
    assert data["decision"] == "ALLOW"

def test_predict_invalid_payload():
    """Verify that invalid payloads are caught by Pydantic validation."""
    # Missing required field 'amount'
    payload = {
        "transaction_id": "api_test_fail_001",
        "user_id": "user_123"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
