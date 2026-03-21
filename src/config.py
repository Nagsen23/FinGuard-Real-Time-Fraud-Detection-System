import os

class Config:
    """Project-wide settings and environment variables."""
    PROJECT_NAME = "Modern Fraud Detection System"
    API_V1_STR = "/api/v1"
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fraud_audit.db")
    
    # Model Configuration
    SUPERVISED_MODEL_PATH = "models/supervised_model.joblib"
    ANOMALY_MODEL_PATH = "models/anomaly_model.joblib"
    
settings = Config()
