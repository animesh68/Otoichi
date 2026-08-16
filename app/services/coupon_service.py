import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, Union
from beanie.odm.operators.update.general import Inc

from app.core.exceptions import BadRequestException, InvalidCouponException, NotFoundException
from app.db.models.social_and_promo import Coupon


class CouponService:
    def __init__(self, db=None):
        self.db = db

    async def get_and_validate_coupon(
        self,
        code: str,
        subtotal: float,
        for_update: bool = False,
    ) -> Tuple[Coupon, float]:
        """
        Validate coupon against rules and return (Coupon, calculated_discount_amount).
        Calculated discount will never exceed subtotal (preventing negative totals).
        """
        coupon = await Coupon.find_one(Coupon.code == code.strip().upper())

        if not coupon:
            raise InvalidCouponException(message=f"Coupon code '{code}' does not exist")

        if not coupon.is_active:
            raise InvalidCouponException(message="Coupon is inactive")

        now = datetime.now(timezone.utc)
        if coupon.expires_at:
            exp = coupon.expires_at if coupon.expires_at.tzinfo else coupon.expires_at.replace(tzinfo=timezone.utc)
            if exp < now:
                raise InvalidCouponException(message="Coupon has expired")

        if coupon.usage_limit is not None and coupon.times_used >= coupon.usage_limit:
            raise InvalidCouponException(message="Coupon usage limit has been reached")

        # Calculate discount
        if coupon.discount_type == "percent":
            discount_amount = round((subtotal * float(coupon.value)) / 100.0, 2)
        elif coupon.discount_type == "fixed":
            discount_amount = round(float(coupon.value), 2)
        else:
            raise BadRequestException(message=f"Unknown coupon discount type: {coupon.discount_type}")

        # Ensure discount never exceeds subtotal
        discount_amount = min(discount_amount, subtotal)
        discount_amount = max(discount_amount, 0.0)

        return coupon, discount_amount

    async def increment_coupon_usage(self, coupon_id: Union[uuid.UUID, str]) -> None:
        """Atomically increment the times_used counter of a coupon."""
        c_id = uuid.UUID(str(coupon_id)) if isinstance(coupon_id, str) else coupon_id
        coupon = await Coupon.find_one(Coupon.id == c_id)
        if coupon:
            if coupon.usage_limit is not None and coupon.times_used >= coupon.usage_limit:
                raise InvalidCouponException(message="Coupon usage limit reached during checkout")
            await coupon.update(Inc({Coupon.times_used: 1}))
