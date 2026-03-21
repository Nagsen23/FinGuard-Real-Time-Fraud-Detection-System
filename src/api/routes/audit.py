"""
src/api/routes/audit.py
------------------------
FastAPI route for inspecting prediction audit logs.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from src.services.audit_service import audit_service

router = APIRouter()

@router.get("/audit/recent", response_model=List[Dict[str, Any]])
async def recent_audits(limit: int = Query(default=20, gt=0, le=100)):
    """
    Get the most recent fraud detection results from the audit log.
    Useful for manual review and monitoring.
    """
    try:
        logs = audit_service.get_recent_predictions(limit=limit)
        return logs
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Audit retrieval error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Could not retrieve recent audit logs"
        )

@router.get("/audit/stats")
async def audit_stats():
    """
    Summary stats for the current audit database.
    (Optional, but helpful for visibility)
    """
    try:
        logs = audit_service.get_recent_predictions(limit=100)
        total = len(logs)
        if total == 0:
            return {"message": "No data available"}
            
        decisions = [l["decision"] for l in logs]
        return {
            "window_size": total,
            "blocks": decisions.count("BLOCK"),
            "reviews": decisions.count("REVIEW"),
            "allows": decisions.count("ALLOW")
        }
    except:
        return {"error": "Stats unavailable"}
