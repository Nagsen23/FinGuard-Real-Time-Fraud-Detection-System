"""
generate_dataset.py  (v2 — Refined)
------------------------------------
Generates 30,000 realistic transactions with strongly learnable fraud patterns.
Fraud ratio: ~3.5%

KEY DESIGN PRINCIPLES IN v2:
─────────────────────────────
A. USER BEHAVIORAL ANCHORING
   Each user is assigned a persistent profile with:
   - 1–2 home cities (they rarely leave)
   - A primary device type (consistent across 95%+ of their transactions)
   - A primary merchant category cluster (spending habits)
   - Whether they are a "local" or "international traveler" (rare)
   This makes behavioral deviation very easy for the model to detect.

B. FRAUD = DEVIATION FROM PROFILE (multi-signal)
   Every fraud transaction combines 2–4 of these deviations:
   - Amount 5x–20x of the user's normal average
   - Night hour (22:00–05:59)
   - Different country from user's home
   - Different device from user's primary device
   - Unusual merchant category for that user
   - Multiple rapid transactions (velocity within 10 minutes)

C. NORMAL = CONSISTENT WITH PROFILE
   Normal transactions stay tightly within profile constraints,
   with only small natural variation in amount, city, time.

All categorical values are bound to the enums in src/api/schemas/request.py.
"""

import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

# ── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# ── Output ───────────────────────────────────────────────────────────────────
OUTPUT_PATH = Path("data/raw/transactions_v2.csv")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Size ─────────────────────────────────────────────────────────────────────
N_TOTAL     = 30_000
FRAUD_RATIO = 0.035
N_FRAUD     = int(N_TOTAL * FRAUD_RATIO)   # ≈1,050
N_NORMAL    = N_TOTAL - N_FRAUD

# ── Categorical pools (enum-aligned) ────────────────────────────────────────
TRANSACTION_TYPES   = ["purchase", "withdrawal", "transfer", "refund", "payment"]
MERCHANT_CATEGORIES = ["retail", "electronics", "grocery", "travel", "dining",
                        "healthcare", "entertainment", "online", "atm", "other"]
DEVICE_TYPES        = ["mobile", "desktop", "tablet", "atm", "pos_terminal", "unknown"]
CHANNELS            = ["online", "in_store", "mobile_app", "atm", "call_center"]
COUNTRIES           = ["US", "IN", "GB", "DE", "AU", "CA", "FR", "SG", "AE", "BR"]

COUNTRY_CITIES = {
    "US": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Dallas", "Seattle"],
    "IN": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune"],
    "GB": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow"],
    "DE": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne"],
    "AU": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "CA": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
    "FR": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice"],
    "SG": ["Singapore City"],
    "AE": ["Dubai", "Abu Dhabi"],
    "BR": ["São Paulo", "Rio de Janeiro", "Brasília"],
}

# Pre-generate merchant IDs per category
MERCHANT_POOL = {
    cat: [f"mrc_{cat[:4]}_{i:04d}" for i in range(1, 101)]
    for cat in MERCHANT_CATEGORIES
}

# Date range (90 days)
END_DT   = datetime(2026, 3, 19, 23, 59, 59)
START_DT = END_DT - timedelta(days=90)


# ── USER PROFILES ────────────────────────────────────────────────────────────
N_USERS = 3_000

def build_user_profiles(n: int) -> dict:
    """
    Each user gets a deterministic behavioral profile that normal transactions
    must conform to so the model can spot any deviation.
    """
    profiles = {}
    for i in range(1, n + 1):
        uid     = f"user_{i:05d}"
        country = random.choice(COUNTRIES)
        cities  = random.sample(COUNTRY_CITIES[country],
                                k=min(2, len(COUNTRY_CITIES[country])))
        # Primary spending clusters — each user focuses on 2–3 categories
        prim_cat = random.sample(MERCHANT_CATEGORIES, k=random.randint(2, 3))
        prim_dev = random.choice(["mobile", "desktop", "tablet", "pos_terminal"])
        # Average spend per transaction (log-normally distributed across users)
        avg_amount = round(float(np.random.lognormal(4.8, 0.8)), 2)  # ~$60–$2,500

        profiles[uid] = {
            "country":         country,
            "cities":          cities,                 # 1–2 home cities
            "primary_device":  prim_dev,
            "primary_cats":    prim_cat,               # preferred categories
            "avg_amount":      max(20.0, avg_amount),  # baseline normal spend
            "channel_pool":    _device_to_channels(prim_dev),
        }
    return profiles

def _device_to_channels(device: str) -> list[str]:
    """Map a primary device to realistic channel options."""
    return {
        "mobile":       ["mobile_app", "online"],
        "desktop":      ["online", "call_center"],
        "tablet":       ["mobile_app", "online"],
        "pos_terminal": ["in_store", "atm"],
    }.get(device, ["online"])

USER_IDS      = [f"user_{i:05d}" for i in range(1, N_USERS + 1)]
USER_PROFILES = build_user_profiles(N_USERS)


# ── Timestamp helpers ────────────────────────────────────────────────────────
def _ts_daytime(day_offset: int = -1) -> datetime:
    """Business-hours timestamp: 07:00–21:00, weighted toward mid-day."""
    day  = random.randint(0, 89) if day_offset < 0 else day_offset
    hour = int(np.random.triangular(7, 13, 21))    # peak around 1 PM
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return START_DT + timedelta(days=day, hours=hour, minutes=minute, seconds=second)

def _ts_night(day_offset: int = -1) -> datetime:
    """Night timestamp: 22:00–05:59 (high-risk window)."""
    day   = random.randint(0, 89) if day_offset < 0 else day_offset
    hour  = random.choice([22, 23, 0, 1, 2, 3, 4, 5])
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return START_DT + timedelta(days=day, hours=hour, minutes=minute, seconds=second)

def _make_id() -> str:
    return f"tx_{uuid.uuid4().hex[:12]}"


# ═══════════════════════════════════════════════════════════════════════════
# NORMAL TRANSACTION GENERATOR
# ═══════════════════════════════════════════════════════════════════════════
def _normal_tx(uid: str, ts: datetime | None = None) -> dict:
    """
    A legitimate transaction stays entirely within the user's profile:
    - City is one of 1–2 home cities
    - Device matches primary device (with 5% natural variance)
    - Amount is ±50% of user's average (log-normal jitter)
    - Merchant category from user's preferred cluster
    - Channel consistent with device
    """
    p       = USER_PROFILES[uid]
    city    = random.choice(p["cities"])
    # 5% chance of using a different device (natural variation, not fraud)
    device  = (p["primary_device"]
               if random.random() > 0.05
               else random.choice(["mobile", "desktop", "tablet"]))
    cat     = random.choice(p["primary_cats"])
    channel = random.choice(p["channel_pool"])

    # Amount: log-normal around user's avg, clamped to sane range
    amount  = round(float(np.random.lognormal(
        mean=np.log(p["avg_amount"]), sigma=0.5)), 2)
    amount  = max(5.0, min(amount, p["avg_amount"] * 3))

    tx_type = random.choices(
        TRANSACTION_TYPES,
        weights=[60, 8, 12, 5, 15],
    )[0]

    card_present = channel in ("in_store", "atm")
    ts = ts or _ts_daytime()

    return {
        "transaction_id":    _make_id(),
        "user_id":           uid,
        "amount":            amount,
        "transaction_type":  tx_type,
        "merchant_category": cat,
        "merchant_id":       random.choice(MERCHANT_POOL[cat]),
        "device_type":       device,
        "channel":           channel,
        "city":              city,
        "country":           p["country"],
        "timestamp":         ts.isoformat(),
        "is_international":  False,
        "card_present":      card_present,
        "is_fraud":          0,
    }


def generate_normal(n: int) -> list[dict]:
    records = []
    for _ in range(n):
        uid = random.choice(USER_IDS)
        records.append(_normal_tx(uid))
    return records


# ═══════════════════════════════════════════════════════════════════════════
# FRAUD PATTERN GENERATORS
# Each pattern intentionally deviates from the user profile on 2+ axes.
# ═══════════════════════════════════════════════════════════════════════════

def _fraud_high_amount_spike(uid: str) -> dict:
    """
    PATTERN: AMOUNT SPIKE
    Amount is 5x–20x the user's normal average spend.
    Combined with night timestamp and an unusual merchant category.
    The large amount + night combo is a strong joint signal.
    """
    p   = USER_PROFILES[uid]
    # Exclude user's normal categories to make it "unusual"
    unusual_cats = [c for c in ["electronics", "travel", "other", "online"]
                    if c not in p["primary_cats"]]
    cat     = random.choice(unusual_cats) if unusual_cats else "other"
    # 5x–20x spike on the user's personal average
    multiplier = random.uniform(5, 20)
    amount  = round(p["avg_amount"] * multiplier, 2)
    ts      = _ts_night()

    return {
        "transaction_id":    _make_id(),
        "user_id":           uid,
        "amount":            amount,
        "transaction_type":  random.choice(["purchase", "transfer"]),
        "merchant_category": cat,
        "merchant_id":       random.choice(MERCHANT_POOL[cat]),
        "device_type":       random.choice(["mobile", "unknown"]),
        "channel":           "online",
        "city":              random.choice(p["cities"]),
        "country":           p["country"],
        "timestamp":         ts.isoformat(),
        "is_international":  False,
        "card_present":      False,
        "is_fraud":          1,
    }


def _fraud_night_transfer(uid: str) -> dict:
    """
    PATTERN: NIGHT TRANSFER / WITHDRAWAL
    High-value transfer or withdrawal between 22:00–05:59.
    User's home country preserved to isolate the time + amount signals.
    """
    p      = USER_PROFILES[uid]
    amount = round(p["avg_amount"] * random.uniform(8, 25), 2)
    ts     = _ts_night()
    cat    = random.choice(["atm", "other", "online"])

    return {
        "transaction_id":    _make_id(),
        "user_id":           uid,
        "amount":            amount,
        "transaction_type":  random.choice(["transfer", "withdrawal"]),
        "merchant_category": cat,
        "merchant_id":       random.choice(MERCHANT_POOL[cat]),
        "device_type":       random.choice(["mobile", "unknown"]),
        "channel":           random.choice(["online", "atm"]),
        "city":              random.choice(p["cities"]),
        "country":           p["country"],
        "timestamp":         ts.isoformat(),
        "is_international":  False,
        "card_present":      False,
        "is_fraud":          1,
    }


def _fraud_international_jump(uid: str) -> dict:
    """
    PATTERN: INTERNATIONAL JUMP
    Transaction from a foreign country the user has never been in (impossible
    to fly there in the time since last home transaction).
    City + country change simultaneously — very strong combined deviation.
    """
    p             = USER_PROFILES[uid]
    # Ensure foreign country is genuinely different
    foreign_cty   = random.choice([c for c in COUNTRIES if c != p["country"]])
    foreign_city  = random.choice(COUNTRY_CITIES[foreign_cty])
    amount        = round(p["avg_amount"] * random.uniform(3, 15), 2)
    cat           = random.choice(["electronics", "travel", "entertainment", "other"])
    ts            = _ts_night()

    return {
        "transaction_id":    _make_id(),
        "user_id":           uid,
        "amount":            amount,
        "transaction_type":  random.choice(["purchase", "withdrawal"]),
        "merchant_category": cat,
        "merchant_id":       random.choice(MERCHANT_POOL[cat]),
        "device_type":       random.choice(["unknown", "mobile"]),
        "channel":           "online",
        "city":              foreign_city,
        "country":           foreign_cty,
        "timestamp":         ts.isoformat(),
        "is_international":  True,
        "card_present":      False,
        "is_fraud":          1,
    }


def _fraud_device_takeover(uid: str) -> dict:
    """
    PATTERN: DEVICE SWITCH (Account Takeover Signal)
    Attacker uses a completely different device from the user's historical primary.
    e.g., user has always used 'mobile' → suddenly 'desktop' or 'unknown'.
    Combined with a large amount and night time to create a strong joint signal.
    """
    p          = USER_PROFILES[uid]
    other_devs = [d for d in ["desktop", "tablet", "unknown"] if d != p["primary_device"]]
    new_device = random.choice(other_devs)
    amount     = round(p["avg_amount"] * random.uniform(4, 12), 2)
    cat        = random.choice([c for c in ["electronics", "online", "other"]
                                if c not in p["primary_cats"]] or ["other"])
    ts         = _ts_night()

    return {
        "transaction_id":    _make_id(),
        "user_id":           uid,
        "amount":            amount,
        "transaction_type":  random.choice(["purchase", "transfer"]),
        "merchant_category": cat,
        "merchant_id":       random.choice(MERCHANT_POOL[cat]),
        "device_type":       new_device,
        "channel":           "online",
        "city":              random.choice(p["cities"]),
        "country":           p["country"],
        "timestamp":         ts.isoformat(),
        "is_international":  False,
        "card_present":      False,
        "is_fraud":          1,
    }


def _fraud_unusual_merchant(uid: str) -> dict:
    """
    PATTERN: UNUSUAL MERCHANT CATEGORY
    User who always shops at grocery/retail suddenly hits 'atm', 'other',
    or 'online' at a large amount.  Category + amount deviation combined.
    """
    p   = USER_PROFILES[uid]
    unusual = [c for c in MERCHANT_CATEGORIES if c not in p["primary_cats"]]
    cat = random.choice(unusual) if unusual else "other"
    amount  = round(p["avg_amount"] * random.uniform(6, 18), 2)
    ts      = _ts_night()

    return {
        "transaction_id":    _make_id(),
        "user_id":           uid,
        "amount":            amount,
        "transaction_type":  "purchase",
        "merchant_category": cat,
        "merchant_id":       random.choice(MERCHANT_POOL[cat]),
        "device_type":       random.choice(["mobile", "unknown"]),
        "channel":           "online",
        "city":              random.choice(p["cities"]),
        "country":           p["country"],
        "timestamp":         ts.isoformat(),
        "is_international":  False,
        "card_present":      False,
        "is_fraud":          1,
    }


def _fraud_rapid_sequence(uid: str) -> list[dict]:
    """
    PATTERN: RAPID VELOCITY (Card Testing / Enumeration Attack)
    3–5 transactions from the same user within a 5–15 minute window.
    Each at a different merchant but same night time window and inflated amount.
    The rapid sequence itself is the primary signal (velocity fraud).
    """
    p        = USER_PROFILES[uid]
    base_ts  = _ts_night()
    n_seq    = random.randint(3, 5)
    records  = []
    elapsed  = 0
    for _ in range(n_seq):
        cat    = random.choice(["online", "electronics", "other"])
        amount = round(p["avg_amount"] * random.uniform(2, 8), 2)
        elapsed += random.randint(1, 4)          # 1–4 minutes between each
        ts     = base_ts + timedelta(minutes=elapsed)

        records.append({
            "transaction_id":    _make_id(),
            "user_id":           uid,
            "amount":            amount,
            "transaction_type":  "purchase",
            "merchant_category": cat,
            "merchant_id":       random.choice(MERCHANT_POOL[cat]),
            "device_type":       random.choice(["mobile", "unknown"]),
            "channel":           "online",
            "city":              random.choice(p["cities"]),
            "country":           p["country"],
            "timestamp":         ts.isoformat(),
            "is_international":  False,
            "card_present":      False,
            "is_fraud":          1,
        })
    return records


# ── Fraud dispatch ───────────────────────────────────────────────────────────
# Weights reflect real-world fraud breakdown
FRAUD_WEIGHTS = {
    "high_amount_spike":   0.22,
    "night_transfer":      0.22,
    "international_jump":  0.22,
    "device_takeover":     0.16,
    "unusual_merchant":    0.10,
    "rapid_sequence":      0.08,
}
_F_NAMES   = list(FRAUD_WEIGHTS.keys())
_F_WEIGHTS = list(FRAUD_WEIGHTS.values())

def generate_fraud(target_n: int) -> list[dict]:
    records = []
    while len(records) < target_n:
        uid     = random.choice(USER_IDS)
        pattern = random.choices(_F_NAMES, weights=_F_WEIGHTS, k=1)[0]
        if pattern == "rapid_sequence":
            records.extend(_fraud_rapid_sequence(uid))
        elif pattern == "high_amount_spike":
            records.append(_fraud_high_amount_spike(uid))
        elif pattern == "night_transfer":
            records.append(_fraud_night_transfer(uid))
        elif pattern == "international_jump":
            records.append(_fraud_international_jump(uid))
        elif pattern == "device_takeover":
            records.append(_fraud_device_takeover(uid))
        elif pattern == "unusual_merchant":
            records.append(_fraud_unusual_merchant(uid))
    return records[:target_n]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
COLUMN_ORDER = [
    "transaction_id", "user_id", "amount", "transaction_type",
    "merchant_category", "merchant_id", "device_type", "channel",
    "city", "country", "timestamp", "is_international", "card_present", "is_fraud",
]

def main():
    print(f"[v2] Building user profiles for {N_USERS:,} users…")

    print(f"  Generating {N_NORMAL:,} normal transactions…")
    normal = generate_normal(N_NORMAL)

    print(f"  Generating {N_FRAUD:,} fraud transactions…")
    fraud  = generate_fraud(N_FRAUD)

    df = pd.DataFrame(normal + fraud)

    # Shuffle
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    # Enforce dtypes
    df["amount"]           = df["amount"].round(2)
    df["is_international"] = df["is_international"].astype(bool)
    df["card_present"]     = df["card_present"].astype(bool)
    df["is_fraud"]         = df["is_fraud"].astype(int)
    df = df[COLUMN_ORDER]

    df.to_csv(OUTPUT_PATH, index=False)


    # ── Report ────────────────────────────────────────────────────────
    fraud_pct = df["is_fraud"].mean() * 100
    print("\n" + "=" * 60)
    print(f"  Saved         : {OUTPUT_PATH}")
    print(f"  Total rows    : {len(df):,}")
    print(f"  Fraud rows    : {df['is_fraud'].sum():,}  ({fraud_pct:.2f}%)")
    print(f"  Users         : {df['user_id'].nunique():,}")
    print(f"  Date range    : {df['timestamp'].min()[:10]} → {df['timestamp'].max()[:10]}")

    print("\n  Amount stats (normal vs fraud):")
    print(df.groupby("is_fraud")["amount"]
            .agg(["min", "mean", "median", "max"])
            .rename(index={0: "Normal", 1: "Fraud"}).round(2).to_string())

    print("\n  Night transactions (is_fraud=1 vs 0):")
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    df["is_night"] = df["hour"].apply(lambda h: 1 if h >= 22 or h < 6 else 0)
    print(df.groupby("is_fraud")["is_night"].mean().rename({0:"Normal",1:"Fraud"}).round(3))

    print("\n  International flag breakdown:")
    print(df.groupby("is_fraud")["is_international"].mean().rename({0:"Normal",1:"Fraud"}).round(3))
    print("=" * 60)


if __name__ == "__main__":
    main()
