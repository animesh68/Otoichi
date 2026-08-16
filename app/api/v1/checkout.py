from datetime import datetime, timezone
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import BadRequestException
from app.db.models.order import Order
from app.db.models.user import User
from app.schemas.checkout import CheckoutRequest, CheckoutSummaryResponse, PaymentIntentResponse, ZeroTotalOrderRequest
from app.schemas.order import OrderResponse
from app.services.order_service import OrderService
from app.services.payment_service import payment_service

logger = logging.getLogger(__name__)

checkout_router = APIRouter(prefix="/checkout", tags=["Checkout"])


@checkout_router.post("/summary", response_model=CheckoutSummaryResponse)
async def get_checkout_summary(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get authoritative server-side pricing breakdown, shipping rate, and coupon discount.
    """
    order_service = OrderService()
    summary = await order_service.calculate_checkout_summary(
        user_id=current_user.id,
        coupon_code=req.coupon_code,
    )
    return CheckoutSummaryResponse(
        subtotal=summary["subtotal"],
        shipping=summary["shipping"],
        discount=summary["discount"],
        total=summary["total"],
        currency=summary["currency"],
        item_count=summary["item_count"],
        checkout_id=req.checkout_id or f"chk_{uuid.uuid4().hex[:12]}",
        is_zero_total=summary["is_zero_total"],
    )


@checkout_router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Stripe PaymentIntent for the current user's cart.
    Server is the single source of truth for prices, discounts, and inventory validation.
    """
    order_service = OrderService()
    summary = await order_service.calculate_checkout_summary(
        user_id=current_user.id,
        coupon_code=req.coupon_code,
    )

    checkout_id = req.checkout_id or f"chk_{uuid.uuid4().hex[:12]}"
    idempotency_key = f"idem_{current_user.id}_{checkout_id}"

    # Handle 100% coupon zero-total orders safely
    if summary["is_zero_total"]:
        return PaymentIntentResponse(
            client_secret=None,
            payment_intent_id=None,
            subtotal=summary["subtotal"],
            shipping=summary["shipping"],
            discount=summary["discount"],
            total=0.0,
            currency=summary["currency"],
            checkout_id=checkout_id,
            is_zero_total=True,
        )

    # Address snapshot resolution
    address_snapshot = None
    if req.new_shipping_address:
        address_snapshot = req.new_shipping_address.model_dump()
    elif req.shipping_address_id:
        addr = next((a for a in current_user.addresses if a.id == req.shipping_address_id), None)
        if addr:
            address_snapshot = {
                "line1": addr.line1,
                "line2": addr.line2,
                "city": addr.city,
                "state": addr.state,
                "postal_code": addr.postal_code,
                "country": addr.country,
                "phone": addr.phone,
            }

    # Prepare pending order in database
    existing_order = await Order.find_one(Order.checkout_id == checkout_id)
    if not existing_order:
        order, _ = await order_service.prepare_order_and_items(
            user=current_user,
            shipping_address_id=req.shipping_address_id,
            shipping_address_data=address_snapshot,
            coupon_code=req.coupon_code,
            checkout_id=checkout_id,
        )
        order.idempotency_key = idempotency_key
        await order.insert()
    else:
        order = existing_order
        if address_snapshot:
            order.shipping_address_snapshot = address_snapshot
            await order.save()

    # Metadata for Stripe PaymentIntent
    metadata = {
        "checkout_id": checkout_id,
        "order_id": str(order.id),
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "coupon_code": req.coupon_code or "",
    }

    intent_data = await payment_service.create_payment_intent(
        amount=summary["total"],
        currency=settings.STRIPE_CURRENCY,
        metadata=metadata,
        idempotency_key=idempotency_key,
    )

    # Link Stripe PaymentIntent ID to Order record
    order.stripe_payment_intent_id = intent_data["id"]
    await order.save()

    return PaymentIntentResponse(
        client_secret=intent_data.get("client_secret"),
        payment_intent_id=intent_data.get("id"),
        subtotal=summary["subtotal"],
        shipping=summary["shipping"],
        discount=summary["discount"],
        total=summary["total"],
        currency=summary["currency"],
        checkout_id=checkout_id,
        is_zero_total=False,
    )


@checkout_router.post("/zero-total-order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_zero_total_order(
    req: ZeroTotalOrderRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Direct fulfillment endpoint for orders that have a $0.00 balance due to full promotional coupons.
    """
    order_service = OrderService()
    address_snapshot = None
    if req.new_shipping_address:
        address_snapshot = req.new_shipping_address.model_dump()

    order = await order_service.create_zero_total_order(
        user=current_user,
        shipping_address_id=req.shipping_address_id,
        shipping_address_data=address_snapshot,
        coupon_code=req.coupon_code,
    )
    return order


@checkout_router.post("/direct-order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_direct_order(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Direct checkout helper for testing / administrative creation.
    """
    order_service = OrderService()
    address_snapshot = None
    if req.new_shipping_address:
        address_snapshot = req.new_shipping_address.model_dump()

    order, product_quantities = await order_service.prepare_order_and_items(
        user=current_user,
        shipping_address_id=req.shipping_address_id,
        shipping_address_data=address_snapshot,
        coupon_code=req.coupon_code,
    )
    for product, qty in product_quantities:
        await order_service.inventory_service.lock_and_decrement_stock(product.id, qty)

    if order.coupon_id:
        await order_service.coupon_service.increment_coupon_usage(order.coupon_id)

    order.status = "paid"
    order.payment_status = "succeeded"
    order.paid_at = datetime.now(timezone.utc)
    await order.insert()

    from app.db.models.cart import CartItem
    await CartItem.find(CartItem.user_id == current_user.id).delete()
    return order


@checkout_router.post("/complete", response_model=OrderResponse)
async def complete_mock_checkout(
    payload: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Development completion helper (when webhooks are not locally connected in dev mock mode).
    In production, webhook is the authoritative fulfillment source.
    """
    payment_intent_id = payload.get("payment_intent_id")
    order_service = OrderService()

    if not payment_intent_id:
        raise BadRequestException(message="payment_intent_id is required")

    order = await order_service.fulfill_paid_order(
        payment_intent_id=payment_intent_id,
        payment_method_type="card",
        metadata={"user_id": str(current_user.id)},
    )
    if not order:
        order = await Order.find_one(Order.user_id == current_user.id, Order.stripe_payment_intent_id == payment_intent_id)

    if not order:
        raise BadRequestException(message="Order fulfillment failed")

    return order
