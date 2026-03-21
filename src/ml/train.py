"""
src/ml/train.py
----------------
End-to-end training pipeline:
  1. Load raw CSV
  2. Fit the FeaturePipeline (preprocessing)
  3. Train the SupervisedModel (XGBoost / RF)
  4. Train the AnomalyDetector (IsolationForest)
  5. Save all artifacts to models/

Run:
    python -m src.ml.train
"""

import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    precision_recall_curve,
    f1_score,
)

from src.ml.feature_pipeline import FeaturePipeline, FEATURE_COLUMNS, CATEGORICAL_COLS, NUMERIC_COLS
from src.ml.supervised_model import SupervisedModel
from src.ml.anomaly_detection import AnomalyDetector
from src.ml.risk_engine import RiskEngine, DEFAULT_THRESHOLDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger(__name__)


# ── Paths ────────────────────────────────────────────────────────────────────
# Try transactions_v2.csv first (refined dataset), fallback to transactions.csv
DATA_DIR   = Path("data/raw")
CANDIDATES = ["transactions_v2.csv", "transactions.csv"]
DATA_PATH  = None
for name in CANDIDATES:
    p = DATA_DIR / name
    if p.exists():
        DATA_PATH = p
        break

MODEL_DIR  = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

SUPERVISED_PATH   = MODEL_DIR / "supervised_model.joblib"
ANOMALY_PATH      = MODEL_DIR / "anomaly_model.joblib"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.joblib"
METADATA_PATH     = MODEL_DIR / "metadata.json"


# ══════════════════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════════════════

def load_dataset(path: Path) -> pd.DataFrame:
    """Load and basic sanity check."""
    logger.info("Loading dataset from %s …", path)
    df = pd.read_csv(path)
    logger.info("  Rows: %d | Columns: %s", len(df), list(df.columns))
    logger.info("  Fraud ratio: %.2f%%", df["is_fraud"].mean() * 100)
    return df


def run_training(data_path: Path | None = None) -> dict:
    """
    Execute the full training pipeline.
    Returns a summary dict of metrics and paths.
    """
    path = data_path or DATA_PATH
    if path is None or not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}. Run generate_dataset.py first.")

    # ── 1. Load ──────────────────────────────────────────────────────
    df = load_dataset(path)
    records = df.to_dict("records")
    y_full  = df["is_fraud"].values

    # ── 2. Fit Feature Pipeline ──────────────────────────────────────
    logger.info("Fitting FeaturePipeline on %d rows…", len(records))
    pipeline = FeaturePipeline()
    X_full   = pipeline.fit_transform(records)
    logger.info("  Feature shape: %s", X_full.shape)

    # ── 3. Train / Eval split (stratified) ───────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X_full, y_full,
        test_size=0.2,
        stratify=y_full,
        random_state=42,
    )
    logger.info("  Train: %d | Test: %d", len(X_train), len(X_test))

    # ── 4. Supervised Model ──────────────────────────────────────────
    sup_model = SupervisedModel()
    sup_model.train(X_train, pd.Series(y_train))

    y_proba = sup_model.predict_proba(X_test)
    y_pred  = (y_proba >= 0.5).astype(int)

    auc = roc_auc_score(y_test, y_proba)
    f1  = f1_score(y_test, y_pred)
    logger.info("  Supervised — AUC: %.4f | F1: %.4f", auc, f1)
    logger.info("\n%s", classification_report(y_test, y_pred, target_names=["normal", "fraud"]))

    # ── 5. Anomaly Detector ──────────────────────────────────────────
    anomaly = AnomalyDetector()
    anomaly.train(X_train)

    anomaly_scores_test = anomaly.predict_anomaly_score(X_test)
    logger.info("  Anomaly score range on test: [%.4f, %.4f]",
                 anomaly_scores_test.min(), anomaly_scores_test.max())

    # ── 6. Risk Engine sanity check ──────────────────────────────────
    engine  = RiskEngine()
    results = [
        engine.evaluate(fp, as_)
        for fp, as_ in zip(y_proba, anomaly_scores_test)
    ]
    decisions = [r.decision for r in results]
    logger.info("  Risk engine decisions on test set:")
    for d in ("ALLOW", "REVIEW", "BLOCK"):
        logger.info("    %s: %d", d, decisions.count(d))

    # ── 7. Save artifacts ────────────────────────────────────────────
    pipeline.save(str(PREPROCESSOR_PATH))
    sup_model.save(str(SUPERVISED_PATH))
    anomaly.save(str(ANOMALY_PATH))
    logger.info("Artifacts saved to %s/", MODEL_DIR)

    # ── 8. Metadata ──────────────────────────────────────────────────
    t = DEFAULT_THRESHOLDS
    metadata = {
        "model_version": "1.0.0",
        "training_timestamp": datetime.now().isoformat(),
        "dataset_path": str(path),
        "dataset_rows": len(df),
        "fraud_ratio": round(float(df["is_fraud"].mean()), 4),
        "feature_names": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLS,
        "numeric_columns": NUMERIC_COLS,
        "algorithms": {
            "supervised": sup_model.algorithm,
            "anomaly": "IsolationForest",
        },
        "metrics": {
            "supervised_auc": round(auc, 4),
            "supervised_f1": round(f1, 4),
        },
        "thresholds": {
            "low_max": t.low_max,
            "medium_max": t.medium_max,
            "high_max": t.high_max,
            "alpha": t.alpha,
            "beta": t.beta,
        },
        "artifacts": {
            "supervised_model": str(SUPERVISED_PATH),
            "anomaly_model": str(ANOMALY_PATH),
            "preprocessor": str(PREPROCESSOR_PATH),
        },
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2))
    logger.info("Metadata written → %s", METADATA_PATH)
    logger.info("═" * 50)
    logger.info("  Training complete!")
    logger.info("═" * 50)

    return metadata


# ═════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_training()
