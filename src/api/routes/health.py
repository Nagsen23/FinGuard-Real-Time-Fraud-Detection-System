"""
src/api/routes/health.py
-------------------------
System health and diagnostic routes.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Basic liveness check.
    """
    return {
        "status": "healthy",
        "service": "fraud-detection-api"
    }
