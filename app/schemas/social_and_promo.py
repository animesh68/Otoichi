import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.auth import UserResponse
from app.schemas.product import ProductResponse


# Wishlist
class WishlistAdd(BaseModel):
    product_id: uuid.UUID


class WishlistResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


# Review
class ReviewCreate(BaseModel):
    product_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


# Coupon
class CouponCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    discount_type: str = Field(..., pattern="^(percent|fixed)$")
    value: float = Field(..., gt=0)
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, gt=0)
    is_active: bool = True


class CouponUpdate(BaseModel):
    discount_type: Optional[str] = Field(None, pattern="^(percent|fixed)$")
    value: Optional[float] = Field(None, gt=0)
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class CouponValidateRequest(BaseModel):
    code: str
    subtotal: float = Field(..., ge=0)


class CouponValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_type: str
    value: float
    discount_amount: float
    message: Optional[str] = None


class CouponResponse(BaseModel):
    id: uuid.UUID
    code: str
    discount_type: str
    value: float
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = None
    times_used: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# StockNotification
class StockNotificationCreate(BaseModel):
    email: EmailStr
    product_id: uuid.UUID


class StockNotificationResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    product_id: uuid.UUID
    notified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
