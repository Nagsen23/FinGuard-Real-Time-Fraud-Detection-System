"""
src/services/database.py
-------------------------
SQLite database connection and schema management.
This module provides a thread-safe connection pool or session for the audit log.
"""

import sqlite3
import logging
import os
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "transactions.db"


def init_db():
    """
    Initializes the database schema if it does not exist.
    Creates the 'prediction_audit_logs' table.
    """
    # Ensure the parent directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing database at {DB_PATH.absolute()}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                request_payload TEXT NOT NULL,  -- JSON serialized
                fraud_probability REAL NOT NULL,
                anomaly_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                decision TEXT NOT NULL,
                top_reasons TEXT NOT NULL,       -- JSON serialized
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add index for faster lookup by transaction_id and user_id
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_id ON prediction_audit_logs(transaction_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON prediction_audit_logs(user_id)")
        
        conn.commit()
        logger.info("Database schema initialized successfully.")


@contextmanager
def get_db_connection():
    """
    Context manager to handle SQLite connection and closure.
    """
    conn = sqlite3.connect(DB_PATH)
    # Enable dict-like access to rows
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Automatically initialize on module import for simplicity in this project
# In a larger system, this would be part of a lifecycle startup event.
if __name__ == "__main__":
    init_db()
