from datetime import datetime, timezone
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
    Handle Stripe webhook events with raw payload signature verification and event idempotency.
    Authoritatively fulfills orders, updates inventory, commits coupons, and persists state transitions.
    """
    payload_bytes = await request.body()

    # 1. Verify webhook signature using raw body bytes
    event = payment_service.verify_webhook_signature(
        payload=payload_bytes,
        signature_header=stripe_signature or "",
    )

    event_id = event.get("id")
    event_type = event.get("type")

    if not event_id:
        return {"received": False, "error": "Missing event id"}

    # 2. Check Idempotency - Ignore already-processed events safely
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

    # 4. Handle event types safely
    event_data = event.get("data", {}).get("object", {})
    order_service = OrderService()

    if event_type == "payment_intent.succeeded":
        payment_intent_id = event_data.get("id")
        metadata = event_data.get("metadata", {})
        charges = event_data.get("charges", {}).get("data", [])
        payment_method_type = "card"
        if charges and charges[0].get("payment_method_details"):
            payment_method_type = charges[0]["payment_method_details"].get("type", "card")

        logger.info(f"Processing payment_intent.succeeded for {payment_intent_id}")
        await order_service.fulfill_paid_order(
            payment_intent_id=payment_intent_id,
            payment_method_type=payment_method_type,
            metadata=metadata,
        )

    elif event_type == "payment_intent.processing":
        payment_intent_id = event_data.get("id")
        if payment_intent_id:
            order = await Order.find_one(Order.stripe_payment_intent_id == payment_intent_id)
            if order and order.payment_status != "succeeded":
                order.payment_status = "processing"
                order.updated_at = datetime.now(timezone.utc)
                await order.save()

    elif event_type in ["payment_intent.payment_failed", "payment_intent.canceled"]:
        payment_intent_id = event_data.get("id")
        if payment_intent_id:
            order = await Order.find_one(Order.stripe_payment_intent_id == payment_intent_id)
            if order and order.payment_status != "succeeded":
                order.payment_status = "failed" if "failed" in event_type else "cancelled"
                order.status = "cancelled"
                order.updated_at = datetime.now(timezone.utc)
                await order.save()
                logger.info(f"Marked order {order.id} as {order.payment_status} from {event_type}")

    elif event_type == "charge.refunded":
        charge_obj = event_data
        payment_intent_id = charge_obj.get("payment_intent")
        amount_refunded_cents = charge_obj.get("amount_refunded", 0)
        amount_refunded = round(amount_refunded_cents / 100.0, 2)
        refunded = charge_obj.get("refunded", False)

        if payment_intent_id:
            order = await Order.find_one(Order.stripe_payment_intent_id == payment_intent_id)
            if order:
                now = datetime.now(timezone.utc)
                order.amount_refunded = amount_refunded
                order.refunded_at = now
                if refunded or amount_refunded >= order.total_amount:
                    order.payment_status = "refunded"
                    order.status = "refunded"
                else:
                    order.payment_status = "partially_refunded"
                order.updated_at = now
                await order.save()
                logger.info(f"Processed refund for order {order.id}: ${amount_refunded}")

    elif event_type == "charge.dispute.created":
        dispute = event_data
        charge_id = dispute.get("charge")
        logger.warning(f"Dispute opened on Stripe charge {charge_id}!")

    return {"received": True, "event_id": event_id, "type": event_type}
