import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import BadRequestException
from app.db.models.user import User
from app.schemas.checkout import CheckoutRequest, PaymentIntentResponse
from app.schemas.order import OrderResponse
from app.services.cart_service import CartService
from app.services.coupon_service import CouponService
from app.services.order_service import OrderService
from app.services.payment_service import payment_service

checkout_router = APIRouter(prefix="/checkout", tags=["Checkout"])


@checkout_router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe PaymentIntent for the current user's cart.
    Calculates subtotal, shipping flat rate, and coupon discount server-side.
    """
    cart_service = CartService()
    coupon_service = CouponService()

    cart = await cart_service.get_cart(user_id=current_user.id)
    if not cart.items:
        raise BadRequestException(message="Cannot checkout with an empty cart")

    subtotal = cart.subtotal
    discount_amount = 0.0

    if req.coupon_code:
        _, discount_amount = await coupon_service.get_and_validate_coupon(
            code=req.coupon_code,
            subtotal=subtotal,
            for_update=False,
        )

    shipping_amount = float(settings.FLAT_SHIPPING_RATE)
    total_amount = max(round(subtotal + shipping_amount - discount_amount, 2), 0.0)

    # Create Payment Intent metadata
    metadata = {
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "coupon_code": req.coupon_code or "",
        "shipping_address_id": str(req.shipping_address_id) if req.shipping_address_id else "",
    }

    intent_data = await payment_service.create_payment_intent(
        amount=total_amount,
        currency=settings.DEFAULT_CURRENCY,
        metadata=metadata,
    )

    return PaymentIntentResponse(
        client_secret=intent_data["client_secret"],
        payment_intent_id=intent_data["id"],
        subtotal=subtotal,
        shipping=shipping_amount,
        discount=discount_amount,
        total=total_amount,
        currency=settings.DEFAULT_CURRENCY,
    )


@checkout_router.post("/direct-order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_direct_order(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Direct checkout order creation (convenience endpoint / test mode).
    Locks stock, snapshots prices, applies coupon, and creates order.
    """
    order_service = OrderService()
    address_snapshot = None
    if req.new_shipping_address:
        address_snapshot = req.new_shipping_address.model_dump()

    order = await order_service.create_order_from_cart(
        user=current_user,
        shipping_address_id=req.shipping_address_id,
        shipping_address_data=address_snapshot,
        coupon_code=req.coupon_code,
        status="paid",  # Direct checkout marked as paid
    )
    return order
