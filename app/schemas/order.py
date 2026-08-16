import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    quantity: int
    unit_price_at_purchase: float
    product_title_snapshot: Optional[str] = None
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    customer_email: Optional[str] = None
    status: str
    payment_status: str = "requires_payment_method"
    subtotal_amount: float
    shipping_amount: float
    discount_amount: float
    total_amount: float
    currency: str
    shipping_address_id: Optional[uuid.UUID] = None
    shipping_address_snapshot: Optional[Dict[str, Any]] = None
    stripe_payment_intent_id: Optional[str] = None
    payment_method_type: Optional[str] = None
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    amount_refunded: float = 0.0
    checkout_id: Optional[str] = None
    coupon_code_snapshot: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|paid|processing|shipped|delivered|cancelled|refunded)$")
