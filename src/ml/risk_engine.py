"""
src/ml/risk_engine.py
----------------------
Combines outputs from the supervised classifier and the anomaly detector
into a single risk assessment with a probability, risk level, and operational decision.

All thresholds are centralized here for easy tuning.
"""

from dataclasses import dataclass
from typing import Literal


# ── Configurable thresholds (single source of truth) ─────────────────────────
@dataclass
class RiskThresholds:
    """
    Edit these to tune operational sensitivity.
    Score is on a [0, 1] scale where 1 = maximum risk.
    """
    low_max: float      = 0.20    # 0.00 – 0.20 → low    → ALLOW
    medium_max: float   = 0.50    # 0.21 – 0.50 → medium → REVIEW
    high_max: float     = 0.75    # 0.51 – 0.75 → high   → BLOCK
    # > 0.75                      → critical             → BLOCK

    # Weights for score aggregation (must sum to 1.0)
    # Higher beta allows anomaly detector to trigger REVIEW on its own.
    alpha: float = 0.60   # supervised weight
    beta: float  = 0.40   # anomaly weight


# Module-level defaults
DEFAULT_THRESHOLDS = RiskThresholds()


RiskLevel  = Literal["low", "medium", "high", "critical"]
Decision   = Literal["ALLOW", "REVIEW", "BLOCK"]


@dataclass
class RiskResult:
    """Immutable result container from the risk engine."""
    fraud_probability: float
    anomaly_score: float
    combined_score: float
    risk_level: RiskLevel
    decision: Decision


class RiskEngine:
    """
    Stateless engine that merges model outputs into business decisions.

    Usage::

        engine = RiskEngine()
        result = engine.evaluate(fraud_prob=0.82, anomaly_score=0.65)
        # result.decision → "BLOCK"
    """

    def __init__(self, thresholds: RiskThresholds | None = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def evaluate(
        self,
        fraud_probability: float,
        anomaly_score: float,
    ) -> RiskResult:
        """
        Combine supervised and anomaly scores into a final risk assessment.

        Parameters
        ----------
        fraud_probability : float
            P(fraud) from the supervised model, in [0, 1].
        anomaly_score : float
            Normalized anomaly score from IsolationForest, in [0, 1].

        Returns
        -------
        RiskResult
        """
        t = self.thresholds
        combined = (t.alpha * fraud_probability) + (t.beta * anomaly_score)
        combined = max(0.0, min(1.0, combined))

        risk_level = self._score_to_level(combined)
        decision   = self._level_to_decision(risk_level)

        return RiskResult(
            fraud_probability=round(fraud_probability, 6),
            anomaly_score=round(anomaly_score, 6),
            combined_score=round(combined, 6),
            risk_level=risk_level,
            decision=decision,
        )

    # ------------------------------------------------------------------
    # Internal mapping
    # ------------------------------------------------------------------

    def _score_to_level(self, score: float) -> RiskLevel:
        t = self.thresholds
        if score <= t.low_max:
            return "low"
        if score <= t.medium_max:
            return "medium"
        if score <= t.high_max:
            return "high"
        return "critical"

    @staticmethod
    def _level_to_decision(level: RiskLevel) -> Decision:
        return {
            "low":      "ALLOW",
            "medium":   "REVIEW",
            "high":     "BLOCK",
            "critical": "BLOCK",
        }[level]

    def __repr__(self) -> str:
        t = self.thresholds
        return (f"RiskEngine(α={t.alpha}, β={t.beta}, "
                f"thresholds=[{t.low_max}, {t.medium_max}, {t.high_max}])")
