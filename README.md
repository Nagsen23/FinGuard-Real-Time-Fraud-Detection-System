# Fraud Detection System (AI-powered)

## Overview
A production-ready, real-time transaction risk scoring system designed to evaluate financial transactions for potential fraud. The system uses a hybrid machine learning approach to assign a `fraud_probability`, an `anomaly_score`, and ultimately issue an automated decision (`ALLOW`, `REVIEW`, or `BLOCK`). 

## Features
- **Real-time Fraud Prediction**: Millisecond-latency scoring using supervised and unsupervised models.
- **Risk Scoring Engine**: Combines XGBoost probabilities with Isolation Forest anomaly scores.
- **Automated Decision Logic**: 
  - `ALLOW` (Safe)
  - `REVIEW` (Suspicious, manual investigation required)
  - `BLOCK` (Critical fraud probability)
- **Audit Logging**: Fully persistent, immutable SQLite audit trail of all transactions and decisions.
- **Fintech Dashboard**: A modern, React-based UI for submitting transactions and monitoring live audit logs.
- **Explainable AI**: Returns the top contributing risk factors and their exact weights for full transparency.

## Architecture
- **Frontend**: React + Vite (Vanilla CSS styling with fintech design tokens).
- **Backend**: FastAPI (Python), utilizing modular routers and Pydantic validation.
- **ML Layer**: 
  - Supervised Model (RandomForest/XGBoost logic)
  - Anomaly Detection (Isolation Forest logic)
  - Feature Engineering Pipeline
- **Database**: SQLite (built-in storage service for lightweight audit logging).

## How It Works
1. A user or payment gateway submits a transaction payload.
2. The **FastAPI backend** parses the payload and applies the feature engineering pipeline.
3. The **ML Layer** predicts the absolute fraud risk.
4. The **Risk Engine** distills the scores into an actionable decision.
5. The result is safely stored in the `audit.db` file.
6. The **React Dashboard** displays the real-time result, animating the metrics, and updates the latest recent transactions table.

## API Endpoints

- `POST /api/v1/predict`: Submits a transaction and returns the risk score.
- `GET /api/v1/audit/recent`: Fetches the latest decisions from the SQLite database.
- `GET /api/v1/health`: Checks application and ML model status.

## Sample Request & Response

### Request (`POST /api/v1/predict`)
```json
{
  "transaction_id": "tx_req_1001",
  "user_id": "user_748",
  "merchant_id": "merch_11",
  "amount": 9500.50,
  "transaction_type": "transfer",
  "merchant_category": "other",
  "device_type": "desktop",
  "channel": "online",
  "city": "Unknown",
  "country": "RU",
  "timestamp": "2026-03-23T00:00:00.000Z",
  "is_international": true,
  "card_present": false
}
```

### Response
```json
{
  "transaction_id": "tx_req_1001",
  "fraud_probability": 0.895,
  "anomaly_score": 0.912,
  "risk_level": "critical",
  "decision": "BLOCK",
  "top_reasons": [
    {
      "feature": "high_amount",
      "contribution": 0.65,
      "direction": "increases_risk"
    }
  ],
  "timestamp": "2026-03-23T00:00:01.123Z"
}
```

## Setup Instructions

### 1. Backend Setup (In project root)
```bash
# Create and activate virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn src.api.main:app --reload --port 8000
```
*Backend will run at http://localhost:8000*

### 2. Frontend Setup (In /frontend directory)
```bash
# Navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```
*Frontend dashboard will run at http://localhost:5173*

## Screenshots
*(Add screenshots here)*
- Dashboard UI
- Prediction result
- Audit table

## Future Improvements
- **Real Dataset Integration**: Train local models on massive historical banking datasets.
- **Advanced ML Models**: Implement LightGBM or deep learning embeddings.
- **SHAP Explainability**: Use real SHAP tree explainers for dynamic feature importance.
- **Streaming Transactions**: Hook up Apache Kafka or RabbitMQ for high-throughput queues.
- **Production Deployment**: Containerize with Docker and migrate SQLite to PostgreSQL.
