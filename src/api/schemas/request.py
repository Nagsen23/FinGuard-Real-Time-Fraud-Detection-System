from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal, Optional
from enum import Enum


class TransactionType(str, Enum):
    purchase = "purchase"
    withdrawal = "withdrawal"
    transfer = "transfer"
    refund = "refund"
    payment = "payment"


class MerchantCategory(str, Enum):
    retail = "retail"
    electronics = "electronics"
    grocery = "grocery"
    travel = "travel"
    dining = "dining"
    healthcare = "healthcare"
    entertainment = "entertainment"
    online = "online"
    atm = "atm"
    other = "other"


class DeviceType(str, Enum):
    mobile = "mobile"
    desktop = "desktop"
    tablet = "tablet"
    atm = "atm"
    pos_terminal = "pos_terminal"
    unknown = "unknown"


class Channel(str, Enum):
    online = "online"
    in_store = "in_store"
    mobile_app = "mobile_app"
    atm = "atm"
    call_center = "call_center"


class TransactionRequest(BaseModel):
    """
    Full transaction input schema used for real-time fraud scoring.
    All fields are validated at the API boundary to ensure downstream pipeline safety.
    """

    # --- Core Identifiers ---
    transaction_id: str = Field(
        ...,
        description="Unique transaction identifier (UUID or external system ID)",
        examples=["tx_abc123"],
    )
    user_id: str = Field(
        ...,
        description="Unique identifier for the user account",
        examples=["user_9812"],
    )
    merchant_id: str = Field(
        ...,
        description="Unique identifier for the merchant",
        examples=["merchant_4409"],
    )

    # --- Transaction Attributes ---
    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount in the account's base currency",
        examples=[124.99],
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of the transaction",
    )
    merchant_category: MerchantCategory = Field(
        ...,
        description="Business category of the merchant",
    )

    # --- Session / Device Context ---
    device_type: DeviceType = Field(
        default=DeviceType.unknown,
        description="Type of device used to initiate the transaction",
    )
    channel: Channel = Field(
        ...,
        description="Channel through which the transaction was made",
    )

    # --- Geographic Information ---
    city: str = Field(
        ...,
        description="City where the transaction occurred",
        examples=["Mumbai"],
    )
    country: str = Field(
        ...,
        description="ISO 3166-1 alpha-2 country code",
        examples=["IN"],
        min_length=2,
        max_length=2,
        pattern="^[a-zA-Z]{2}$",
    )

    # --- Temporal ---
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="ISO 8601 timestamp of when the transaction was initiated",
    )

    # --- Risk Signals ---
    is_international: bool = Field(
        default=False,
        description="True if the transaction crosses country boundaries",
    )
    card_present: bool = Field(
        default=True,
        description="True if the physical card was used (False for card-not-present / online)",
    )

    @field_validator("country")
    @classmethod
    def country_must_be_uppercase(cls, v: str) -> str:
        """Normalize country codes to uppercase."""
        return v.upper()

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: float) -> float:
        """Round to 2 decimal places to prevent floating point inconsistencies."""
        return round(v, 2)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "transaction_id": "tx_prod_demo_001",
                    "user_id": "user_101",
                    "merchant_id": "merchant_50",
                    "amount": 125.50,
                    "transaction_type": "purchase",
                    "merchant_category": "retail",
                    "device_type": "mobile",
                    "channel": "mobile_app",
                    "city": "New York",
                    "country": "US",
                    "timestamp": "2026-03-20T10:00:00Z",
                    "is_international": False,
                    "card_present": False,
                }
            ]
        }
    }
