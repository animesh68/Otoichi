from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
import pymongo
from pydantic import Field
from beanie import Document, Indexed


class Wishlist(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(index=True)
    product_id: uuid.UUID = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "wishlists"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("product_id", pymongo.ASCENDING)],
                unique=True,
            )
        ]


class Review(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(index=True)
    product_id: uuid.UUID = Field(index=True)
    user_name: Optional[str] = None
    rating: int  # 1 to 5
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "reviews"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("product_id", pymongo.ASCENDING)],
                unique=True,
            )
        ]


class Coupon(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    code: Indexed(str, unique=True)
    discount_type: str  # "percent", "fixed"
    value: float
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = None
    times_used: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "coupons"


class StockNotification(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: str = Field(index=True)
    product_id: uuid.UUID = Field(index=True)
    notified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "stock_notifications"
        indexes = [
            pymongo.IndexModel(
                [("email", pymongo.ASCENDING), ("product_id", pymongo.ASCENDING)],
                unique=True,
            )
        ]


class StripeWebhookEvent(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_id: Indexed(str, unique=True)
    event_type: str
    payload: Optional[Dict[str, Any]] = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "stripe_webhook_events"
