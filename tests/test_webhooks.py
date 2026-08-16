import json
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_stripe_webhook_payment_intent_succeeded(client: AsyncClient, seed_data, auth_headers_customer):
    """Test webhook successfully creates order from cart and is idempotent on duplicate delivery."""
    customer = seed_data["customer"]
    product = seed_data["product_album"]

    # Customer has 1 item in cart
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=auth_headers_customer,
    )

    event_payload = {
        "id": "evt_test_success_123456",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123456",
                "amount": 3499,
                "currency": "usd",
                "status": "succeeded",
                "metadata": {
                    "user_id": str(customer.id),
                    "shipping_address_id": "",
                    "coupon_code": "",
                },
            }
        },
    }

    # First delivery
    res1 = await client.post(
        "/api/v1/webhooks/stripe",
        content=json.dumps(event_payload),
        headers={"Content-Type": "application/json"},
    )
    assert res1.status_code == 200
    assert res1.json()["received"] is True

    # Duplicate delivery (same event ID) -> Idempotent, no duplicate order or stock decrement
    res2 = await client.post(
        "/api/v1/webhooks/stripe",
        content=json.dumps(event_payload),
        headers={"Content-Type": "application/json"},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "already_processed"


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_payload(client: AsyncClient):
    """Test webhook with invalid body returns error."""
    res = await client.post(
        "/api/v1/webhooks/stripe",
        content="invalid json",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 400
