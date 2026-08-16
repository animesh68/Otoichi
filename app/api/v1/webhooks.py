import logging
import uuid
from typing import Any, Dict
from fastapi import APIRouter, Header, Request

from app.db.models.order import Order
from app.db.models.social_and_promo import StripeWebhookEvent
from app.db.models.user import User
from app.services.order_service import OrderService
from app.services.payment_service import payment_service

logger = logging.getLogger(__name__)

webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@webhooks_router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """
    Handle Stripe webhook events with signature verification and idempotency protection.
    """
    payload_bytes = await request.body()

    # 1. Verify webhook signature
    event = payment_service.verify_webhook_signature(
        payload=payload_bytes,
        signature_header=stripe_signature or "",
    )

    event_id = event.get("id")
    event_type = event.get("type")

    if not event_id:
        return {"received": False, "error": "Missing event id"}

    # 2. Check Idempotency
    existing_event = await StripeWebhookEvent.find_one(StripeWebhookEvent.event_id == event_id)
    if existing_event:
        logger.info(f"Stripe event {event_id} already processed. Skipping.")
        return {"received": True, "status": "already_processed"}

    # 3. Record event in database for idempotency
    webhook_record = StripeWebhookEvent(
        event_id=event_id,
        event_type=event_type or "unknown",
        payload=event.get("data", {}),
    )
    await webhook_record.insert()

    # 4. Process event
    event_data = event.get("data", {}).get("object", {})

    if event_type == "payment_intent.succeeded":
        payment_intent_id = event_data.get("id")
        metadata = event_data.get("metadata", {})
        user_id_str = metadata.get("user_id")

        if user_id_str:
            try:
                user_id = uuid.UUID(user_id_str)
                user = await User.find_one(User.id == user_id)

                if user:
                    existing_order = await Order.find_one(Order.stripe_payment_intent_id == payment_intent_id)
                    if existing_order:
                        if existing_order.status == "pending":
                            existing_order.status = "paid"
                            await existing_order.save()
                    else:
                        shipping_addr_id_str = metadata.get("shipping_address_id")
                        shipping_addr_id = uuid.UUID(shipping_addr_id_str) if shipping_addr_id_str else None
                        coupon_code = metadata.get("coupon_code") or None

                        order_service = OrderService()
                        await order_service.create_order_from_cart(
                            user=user,
                            shipping_address_id=shipping_addr_id,
                            coupon_code=coupon_code,
                            payment_intent_id=payment_intent_id,
                            status="paid",
                        )
            except Exception as e:
                logger.error(f"Error handling payment_intent.succeeded for {payment_intent_id}: {e}")
                pass

    elif event_type == "payment_intent.payment_failed":
        payment_intent_id = event_data.get("id")
        if payment_intent_id:
            order = await Order.find_one(Order.stripe_payment_intent_id == payment_intent_id)
            if order and order.status == "pending":
                order.status = "cancelled"
                await order.save()

    return {"received": True}
