"""
src/ml/explainer_lite.py
-------------------------
Lightweight, rule-based explanation engine to provide human-readable reasons 
for fraud flags without the overhead of SHAP.
"""

from typing import List, Dict, Any
from src.ml.risk_engine import RiskResult

def get_top_reasons(transaction: Dict[str, Any], risk_result: RiskResult) -> List[Dict[str, Any]]:
    """
    Analyzes the transaction and risk scores to identify the most likely 
    reasons for a fraud flag.
    Returns a list of dicts matching the TopReason schema.
    """
    reasons = []
    
    amount = transaction.get("amount", 0)
    if amount > 10000:
        reasons.append({
            "feature": "high_amount",
            "contribution": 0.5,
            "direction": "increases_risk"
        })
    elif amount > 5000:
        reasons.append({
            "feature": "high_amount",
            "contribution": 0.25,
            "direction": "increases_risk"
        })

    # 2. Temporal Signal
    ts_str = transaction.get("timestamp")
    if ts_str:
        try:
            from datetime import datetime
            ts = datetime.fromisoformat(ts_str.replace('Z', ''))
            if ts.hour >= 22 or ts.hour <= 5:
                reasons.append({
                    "feature": "night_transaction",
                    "contribution": 0.3,
                    "direction": "increases_risk"
                })
            else:
                reasons.append({
                    "feature": "daytime_transaction",
                    "contribution": 0.1,
                    "direction": "decreases_risk"
                })
        except:
            pass

    # 3. Geo/International Signal
    if transaction.get("is_international", False):
        reasons.append({
            "feature": "international_transaction",
            "contribution": 0.2,
            "direction": "increases_risk"
        })
    else:
        reasons.append({
            "feature": "domestic_transaction",
            "contribution": 0.1,
            "direction": "decreases_risk"
        })
    
    # 4. Channel/Physical Signal
    if not transaction.get("card_present", True):
        reasons.append({
            "feature": "card_not_present",
            "contribution": 0.15,
            "direction": "increases_risk"
        })

    # 5. Device Signal
    device = transaction.get("device_type", "unknown").lower()
    if device == "unknown":
        reasons.append({
            "feature": "unusual_device",
            "contribution": 0.1,
            "direction": "increases_risk"
        })

    # Return top 3 most relevant reasons
    # Sort by contribution descending
    sorted_reasons = sorted(reasons, key=lambda x: x["contribution"], reverse=True)
    
    if not sorted_reasons:
        return [{
            "feature": "domestic_transaction",
            "contribution": 0.0,
            "direction": "decreases_risk"
        }]

    return sorted_reasons[:3]
