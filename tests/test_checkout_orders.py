import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_checkout_create_payment_intent(client: AsyncClient, seed_data, auth_headers_customer):
    """Test Stripe PaymentIntent creation with coupon and flat shipping calculation."""
    product = seed_data["product_album"]  # price = 29.99

    # Add item to cart
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=auth_headers_customer,
    )

    # Create PaymentIntent with 10% coupon
    res = await client.post(
        "/api/v1/checkout/create-intent",
        json={"coupon_code": "SAVE10"},
        headers=auth_headers_customer,
    )
    assert res.status_code == 200
    data = res.json()
    assert "client_secret" in data
    assert "payment_intent_id" in data
    assert data["subtotal"] == 29.99
    assert data["shipping"] == 5.0
    assert data["discount"] == 3.0  # 10% of 29.99 rounded
    assert data["total"] == round(29.99 + 5.0 - 3.0, 2)


@pytest.mark.asyncio
async def test_direct_order_creation_and_price_snapshot(client: AsyncClient, seed_data, auth_headers_customer):
    """Test order creation, cart clearance, and frozen historical price snapshot."""
    product = seed_data["product_album"]  # price = 29.99

    # Add to cart
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=auth_headers_customer,
    )

    # Direct order checkout
    order_res = await client.post(
        "/api/v1/checkout/direct-order",
        json={"coupon_code": "SAVE5"},
        headers=auth_headers_customer,
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["status"] == "paid"
    assert order_data["subtotal_amount"] == 59.98
    assert order_data["shipping_amount"] == 5.0
    assert order_data["discount_amount"] == 5.0
    assert order_data["total_amount"] == 59.98
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["unit_price_at_purchase"] == 29.99
    assert order_data["items"][0]["quantity"] == 2

    # Verify cart was cleared
    cart_check = await client.get("/api/v1/cart/", headers=auth_headers_customer)
    assert cart_check.json()["total_items"] == 0


@pytest.mark.asyncio
async def test_order_status_transitions(client: AsyncClient, seed_data, auth_headers_customer, auth_headers_admin):
    """Test order state transition rules and protections."""
    product = seed_data["product_album"]

    # Place order
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=auth_headers_customer,
    )
    order_res = await client.post(
        "/api/v1/checkout/direct-order",
        json={},
        headers=auth_headers_customer,
    )
    order_id = order_res.json()["id"]

    # Admin transitions: paid -> shipped (Allowed)
    shipped_res = await client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "shipped"},
        headers=auth_headers_admin,
    )
    assert shipped_res.status_code == 200
    assert shipped_res.json()["status"] == "shipped"

    # Admin transitions: shipped -> delivered (Allowed)
    delivered_res = await client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "delivered"},
        headers=auth_headers_admin,
    )
    assert delivered_res.status_code == 200
    assert delivered_res.json()["status"] == "delivered"

    # Admin transitions: delivered -> pending (Illegal / Rejected)
    illegal_res = await client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "pending"},
        headers=auth_headers_admin,
    )
    assert illegal_res.status_code == 400
    assert illegal_res.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"
