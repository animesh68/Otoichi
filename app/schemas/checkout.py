import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.auth import AddressCreate


class CheckoutRequest(BaseModel):
    shipping_address_id: Optional[uuid.UUID] = None
    new_shipping_address: Optional[AddressCreate] = None
    coupon_code: Optional[str] = None
    checkout_id: Optional[str] = None
    guest_email: Optional[str] = None


class CheckoutSummaryResponse(BaseModel):
    subtotal: float
    shipping: float
    discount: float
    total: float
    currency: str
    item_count: int
    checkout_id: str
    is_zero_total: bool = False


class PaymentIntentResponse(BaseModel):
    client_secret: Optional[str] = None
    payment_intent_id: Optional[str] = None
    subtotal: float
    shipping: float
    discount: float
    total: float
    currency: str
    checkout_id: str
    is_zero_total: bool = False


class ZeroTotalOrderRequest(BaseModel):
    shipping_address_id: Optional[uuid.UUID] = None
    new_shipping_address: Optional[AddressCreate] = None
    coupon_code: str
    checkout_id: Optional[str] = None
    guest_email: Optional[str] = None
