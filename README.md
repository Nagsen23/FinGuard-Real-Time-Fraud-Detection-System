# Fraud Detection System

A scalable, production-ready machine learning system for real-time fraud detection. 
This project integrates an orchestrated training pipeline, a fast real-time inference API, and a persistent audit logging layer.

## 🌟 Key Features

### Machine Learning Engine
- **Hybrid Scoring**: Uses a supervised classifier (XGBoost/RandomForest) to predict known fraud patterns, combined with an unsupervised anomaly detector (IsolationForest) to catch novel/unknown threats.
- **Risk Engine**: Normalizes and combines probability scores into a unified `risk_level` (low, medium, high, critical) and makes a final business decision (`ALLOW`, `REVIEW`, `BLOCK`).
- **Feature Engineering**: Comprehensive pipeline (`FeaturePipeline`) to transform categorical, numeric, temporal, and Boolean fields into a robust numeric vector.
- **Explainability**: A lightweight, rule-based explainer (`explainer_lite.py`) that returns business-readable tags (e.g., `high_amount`, `night_transaction`, `international_transaction`) for each prediction flag.
- **Synthetic Data**: Includes a realistic synthetic data generator (`generate_dataset.py`) to simulate user transaction behaviors and intricate fraud patterns.

### Real-Time API
- **FastAPI Backend**: Built for speed, concurrency, and easy maintenance.
- **Strict Validation**: Utilizes Pydantic schemas to validate real-time transaction packets at the API boundary, enforcing correct `transaction_types`, roundings, and ISO-standard `country` logic.
- **Endpoint Structure**:
  - `POST /api/v1/predict` — Analyze a transaction for fraud.
  - `GET /api/v1/health` — Basic service heartbeat.
  - `GET /api/v1/health/models` — Verify ML artifacts are loaded into memory.

### Persistence & Audit Layer
- **SQLite Database**: Automatically configured to run in `./data/transactions.db`.
- **Audit Logging**: Every single prediction is permanently logged, capturing the request payload, risk scores, decisions, and explainability factors.
- **Insight Endpoint**: `GET /api/v1/audit/recent` to query historical transaction logs.
- **Fail-Open Policy**: Built to guarantee high availability; if the logging service fails, it degrades gracefully and still returns the ML decision to the caller.

---

## 🛠️ Project Structure

```text
fraud-detection-system/
├── data/
│   ├── raw/                 # Raw datasets (e.g., transactions.csv)
│   └── transactions.db      # SQLite persistence layer
├── models/                  # Joblib ML artifacts and metadata.json
├── examples/                # Example request and response JSONs
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI application entrypoint
│   │   ├── routes/          # API endpoints (predict, audit, health)
│   │   └── schemas/         # Pydantic data models
│   ├── ml/
│   │   ├── train.py                 # Core training loop
│   │   ├── feature_pipeline.py      # Raw text to ML features
│   │   ├── supervised_model.py      # Classification logic
│   │   ├── anomaly_detection.py     # Unsupervised logic
│   │   ├── explainer_lite.py        # Business logic for human reasons
│   │   ├── inference.py             # Inference encapsulation
│   │   └── risk_engine.py           # ML thresholds
│   └── services/
│       ├── database.py              # SQLite session connections
│       └── audit_service.py         # JSON serialization & database writes
├── tests/                           # Pytest integration & unit regression
├── API_DOCS.md                      # Extensive endpoint reference documentation
└── README.md                        # This file
```

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Generate Data & Train Models
```bash
# 1. Generate the initial synthetic dataset
python generate_dataset.py

# 2. Train the full ML pipeline and generate models
python -m src.ml.train
```

### 3. Start the Server
```bash
python -m src.api.main
```
The server will start on `http://localhost:8000`. 
Interactive Swagger UI documentation is available at `http://localhost:8000/docs`.

### 4. Make a Prediction
Verify the system by executing a prediction call using the `examples/suspicious_transaction.json` payload:

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
     -H "Content-Type: application/json" \
     -d @examples/suspicious_transaction.json
```

---

## 🧪 Testing
The system maintains high coverage via `pytest`. Run the full suite using:
```bash
python -m pytest tests -v
```

This verifies ML pipelines, data encodings, API payload schema routing, and SQLite storage logic.

---

## 📖 API Documentation
For deeper integration, see the fully documented APIs in the [API_DOCS.md](./API_DOCS.md) file.
