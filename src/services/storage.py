import sqlite3
import json
from datetime import datetime
from src.config import settings

class StorageService:
    def __init__(self):
        # Using a simple SQLite setup for the portfolio project
        self.db_name = "transactions.db"
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    amount REAL,
                    risk_score REAL,
                    decision TEXT,
                    explanation TEXT,
                    timestamp DATETIME
                )
            """)
            
    def store_transaction(self, transaction_id, user_id, amount, score, decision, explanation):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                INSERT INTO transactions (transaction_id, user_id, amount, risk_score, decision, explanation, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (transaction_id, user_id, amount, score, decision, json.dumps(explanation), datetime.now()))
