from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from beanie import Document


class OrderItem(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    product_id: uuid.UUID
    quantity: int
    unit_price_at_purchase: float
    product_title_snapshot: str


class Order(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(index=True)
    status: str = "pending"  # "pending", "paid", "shipped", "delivered", "cancelled"
    subtotal_amount: float
    shipping_amount: float
    discount_amount: float = 0.0
    total_amount: float
    currency: str = "USD"
    shipping_address_snapshot: Optional[Dict[str, Any]] = None
    stripe_payment_intent_id: Optional[str] = Field(default=None, index=True)
    coupon_id: Optional[uuid.UUID] = None
    coupon_code_snapshot: Optional[str] = None
    items: List[OrderItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "orders"
