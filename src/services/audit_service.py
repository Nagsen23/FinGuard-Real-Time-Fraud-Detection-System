"""
src/services/audit_service.py
------------------------------
Service for handling the persistence and retrieval of prediction audit logs.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.services.database import get_db_connection, init_db

logger = logging.getLogger(__name__)

class AuditService:
    """
    Business logic for auditing prediction results.
    """
    
    def __init__(self):
        # Ensure DB is ready before use
        init_db()

    def log_prediction(
        self, 
        transaction_id: str, 
        user_id: str, 
        request_payload: Dict[str, Any], 
        prediction_result: Dict[str, Any]
    ) -> bool:
        """
        Persists a single prediction event to the database.
        """
        try:
            # Custom encoder helper for datetime
            def json_serial(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError("Type %s not serializable" % type(obj))

            # Prepare serialization
            payload_json = json.dumps(request_payload, default=json_serial)
            reasons_json = json.dumps(prediction_result.get("top_reasons", []), default=json_serial)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO prediction_audit_logs (
                        transaction_id, user_id, request_payload, 
                        fraud_probability, anomaly_score, risk_level, 
                        decision, top_reasons
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_id,
                    user_id,
                    payload_json,
                    prediction_result.get("fraud_probability", 0.0),
                    prediction_result.get("anomaly_score", 0.0),
                    prediction_result.get("risk_level", "unknown"),
                    prediction_result.get("decision", "REVIEW"),
                    reasons_json
                ))
                conn.commit()
                
            logger.info(f"Audit log saved for transaction: {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log prediction for {transaction_id}: {e}")
            return False

    def get_recent_predictions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent audit logs.
        
        Args:
            limit: Number of records to return
            
        Returns:
            List of log dictionaries.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM prediction_audit_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                
                # Convert rows (sqlite3.Row) to dict and deserialize JSON
                results = []
                for row in rows:
                    r = dict(row)
                    r["request_payload"] = json.loads(r["request_payload"])
                    r["top_reasons"] = json.loads(r["top_reasons"])
                    results.append(r)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to fetch recent audit logs: {e}")
            return []

# Singleton instance for easy access
audit_service = AuditService()
