# Fraud Detection System API Documentation

The Fraud Detection API provides real-time transaction scoring and persistent auditing.

## Base URL
`http://localhost:8000/api/v1`

## Endpoints

### 1. Predict Fraud Risk
**POST** `/predict`

Analyzes a transaction for potential fraud and returns a risk decision. This endpoint automatically persists the request and decision to the audit database.

**Request Body (JSON)**:
```json
{
  "transaction_id": "tx_demo_fraud_002",
  "user_id": "user_88219",
  "merchant_id": "merchant_9911",
  "amount": 12500.00,
  "transaction_type": "transfer",
  "merchant_category": "other",
  "device_type": "desktop",
  "channel": "online",
  "city": "Unknown City",
  "country": "RU",
  "timestamp": "2026-03-21T03:15:00Z",
  "is_international": true,
  "card_present": false
}
```
*Note: `country` must be an exact 2-letter uppercase ISO code.*

**Response (JSON)**:
```json
{
  "transaction_id": "tx_demo_fraud_002",
  "fraud_probability": 0.895,
  "anomaly_score": 0.912,
  "risk_level": "critical",
  "decision": "BLOCK",
  "top_reasons": [
    {
      "feature": "high_amount",
      "contribution": 0.5,
      "direction": "increases_risk"
    },
    {
      "feature": "night_transaction",
      "contribution": 0.3,
      "direction": "increases_risk"
    }
  ],
  "timestamp": "2026-03-21T03:15:02.987654Z"
}
```

**Decision & Risk Levels**:
- `ALLOW`: The transaction is safe (`low` risk).
- `REVIEW`: Suspicious patterns matched; requires manual review (`medium` risk).
- `BLOCK`: High probability of fraud; automated block recommended (`high` or `critical` risk).

---

### 2. Audit Trail
**GET** `/audit/recent`

Retrieves the latest prediction results from the underlying SQLite database.

**Query Parameters**:
- `limit` (int, default=20): Number of recent logs to fetch.

**Response**: List of prediction log objects.

---

### 3. Model Health Check
**GET** `/health/models`

Verifies that the core machine learning artifacts are loaded in memory and the inference engine is ready.

**Response**:
```json
{
  "status": "ready",
  "metadata": {
    "model_version": "1.0",
    "training_timestamp": "2026-03-20T10:00:00Z",
    ...
  }
}
```

### 4. System Health Check
**GET** `/health`

Basic ping endpoint.
