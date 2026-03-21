from src.ml.inference import FraudInference

# Load model
model = FraudInference()

# 🚨 FRAUD TEST CASE (High amount + international + night + card-not-present)
fraud_tx = {
    "transaction_id": "test_001",
    "user_id": "user_999",
    "amount": 20000.0,
    "transaction_type": "purchase",
    "merchant_category": "electronics",
    "merchant_id": "mrc_ele_001",
    "device_type": "desktop",
    "channel": "online",
    "city": "Dubai",
    "country": "AE",
    "timestamp": "2026-03-20T02:30:00",
    "is_international": True,
    "card_present": False
}

# ✅ SAFE TEST CASE (Small amount + local + day + card-present)
safe_tx = {
    "transaction_id": "test_002",
    "user_id": "user_001",
    "amount": 200.0,
    "transaction_type": "purchase",
    "merchant_category": "grocery",
    "merchant_id": "mrc_gro_001",
    "device_type": "mobile",
    "channel": "mobile_app",
    "city": "Mumbai",
    "country": "IN",
    "timestamp": "2026-03-20T14:00:00",
    "is_international": False,
    "card_present": True
}

if __name__ == "__main__":
    print("\n🚨 RUNNING MANUAL INFERENCE TESTS...")
    
    print("\n🚨 FRAUD TEST RESULT:")
    try:
        res_fraud = model.predict(fraud_tx)
        import json
        print(json.dumps(res_fraud, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    print("\n✅ SAFE TEST RESULT:")
    try:
        res_safe = model.predict(safe_tx)
        print(json.dumps(res_safe, indent=2))
    except Exception as e:
        print(f"Error: {e}")
