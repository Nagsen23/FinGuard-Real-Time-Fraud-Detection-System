"""
src/api/main.py
----------------
Main Entrypoint for the Fraud Detection API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import predict, health, audit

app = FastAPI(
    title="Fraud Detection System API",
    description="Production-ready real-time fraud detection service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(predict.router, prefix="/api/v1", tags=["Inference"])
app.include_router(audit.router, prefix="/api/v1", tags=["Audit"])
app.include_router(health.router, prefix="/api/v1", tags=["System"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Fraud Detection System API",
        "docs": "/docs",
        "status": "active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
