import pytest
import os
import json
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.database import DB_PATH, get_db_connection, init_db
from src.services.audit_service import audit_service

import logging
logging.basicConfig(level=logging.INFO)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Ensure the database is initialized before each test."""
    init_db()
    # Optional: Clear the table for clean tests if needed
    with get_db_connection() as conn:
        conn.execute("DELETE FROM prediction_audit_logs")
        conn.commit()

def test_database_initialization():
    """Verify that the database file and table are created."""
    assert os.path.exists(DB_PATH)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_audit_logs'")
        assert cursor.fetchone() is not None

def test_audit_service_log_and_retrieve():
    """Test the AuditService's ability to save and fetch records."""
    payload = {"test": "data"}
    result = {
        "fraud_probability": 0.1,
        "anomaly_score": 0.2,
        "risk_level": "low",
        "decision": "ALLOW",
        "top_reasons": ["test reason"]
    }
    
    success = audit_service.log_prediction(
        transaction_id="tx_test_123",
        user_id="user_test_123",
        request_payload=payload,
        prediction_result=result
    )
    assert success is True
    
    recent = audit_service.get_recent_predictions(limit=1)
    assert len(recent) == 1
    assert recent[0]["transaction_id"] == "tx_test_123"
    assert recent[0]["request_payload"] == payload
    assert recent[0]["top_reasons"] == ["test reason"]

def test_predict_endpoint_logs_to_db():
    """Integration test: Verify that calling /predict creates a DB entry."""
    payload = {
        "transaction_id": "api_audit_test_001",
        "user_id": "user_audit_1",
        "amount": 100.0,
        "merchant_id": "mrc_1",
        "transaction_type": "purchase",
        "merchant_category": "retail",
        "device_type": "mobile",
        "channel": "online",
        "city": "London",
        "country": "GB",
        "is_international": False,
        "card_present": True
    }
    
    # Call predict
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    
    # Check DB
    recent = audit_service.get_recent_predictions(limit=1)
    assert len(recent) == 1
    assert recent[0]["transaction_id"] == "api_audit_test_001"
    assert recent[0]["decision"] == response.json()["decision"]

def test_audit_recent_endpoint():
    """Verify the /audit/recent API endpoint."""
    # Insert a dummy record directly via service
    audit_service.log_prediction("tx_api_1", "u1", {}, {"decision": "ALLOW"})
    
    response = client.get("/api/v1/audit/recent?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["transaction_id"] == "tx_api_1"

def test_audit_logging_graceful_failure():
    """
    Verify that if DB logging fails, the API still returns a success result 
    (graceful handling requirement).
    """
    from unittest.mock import patch
    from src.services.audit_service import AuditService
    
    payload = {
        "transaction_id": "api_fail_test_001",
        "user_id": "user_fail_1",
        "amount": 50.0,
        "merchant_id": "mrc_1",
        "transaction_type": "purchase",
        "merchant_category": "retail",
        "device_type": "mobile",
        "channel": "online",
        "city": "City",
        "country": "US",
        "is_international": False,
        "card_present": True
    }
    
    # Mock log_prediction to return False
    with patch.object(AuditService, 'log_prediction', return_value=False):
        response = client.post("/api/v1/predict", json=payload)
        # Status should still be 200 even if logging failed
        assert response.status_code == 200
        assert "decision" in response.json()
