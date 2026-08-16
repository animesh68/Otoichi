import uuid
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.auth import AddressCreate


class CheckoutRequest(BaseModel):
    shipping_address_id: Optional[uuid.UUID] = None
    new_shipping_address: Optional[AddressCreate] = None
    coupon_code: Optional[str] = None


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    subtotal: float
    shipping: float
    discount: float
    total: float
    currency: str


class CheckoutSummary(BaseModel):
    subtotal: float
    shipping: float
    discount: float
    total: float
    currency: str
    item_count: int
