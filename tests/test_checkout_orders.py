import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_checkout_create_payment_intent(client: AsyncClient, seed_data, auth_headers_customer):
    """Test Stripe PaymentIntent creation with coupon and server-calculated shipping."""
    product = seed_data["product_album"]  # price = 29.99
    expected_shipping = float(settings.FLAT_SHIPPING_RATE)

    # Add item to cart
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=auth_headers_customer,
    )

    # Check summary endpoint
    summary_res = await client.post(
        "/api/v1/checkout/summary",
        json={"coupon_code": "SAVE10"},
        headers=auth_headers_customer,
    )
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["subtotal"] == 29.99
    assert summary_data["shipping"] == expected_shipping
    assert summary_data["discount"] == 3.0
    assert summary_data["total"] == round(29.99 + expected_shipping - 3.0, 2)

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
    assert data["shipping"] == expected_shipping
    assert data["discount"] == 3.0
    assert data["total"] == round(29.99 + expected_shipping - 3.0, 2)


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
    expected_shipping = float(settings.FLAT_SHIPPING_RATE)
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["status"] == "paid"
    assert order_data["subtotal_amount"] == 59.98
    assert order_data["shipping_amount"] == expected_shipping
    assert order_data["discount_amount"] == 5.0
    assert order_data["total_amount"] == round(59.98 + expected_shipping - 5.0, 2)
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


@pytest.mark.asyncio
async def test_zero_total_coupon_order(client: AsyncClient, seed_data, auth_headers_customer):
    """Test 100% discount coupon flow without Stripe intent."""
    from app.db.models.social_and_promo import Coupon
    import uuid

    # Create 100% off coupon
    free_coupon = Coupon(
        id=uuid.uuid4(),
        code="FREE100",
        discount_type="percent",
        value=100.0,
        is_active=True,
    )
    await free_coupon.insert()

    product = seed_data["product_album"]
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=auth_headers_customer,
    )

    # 1. Summary should report is_zero_total == True
    summary_res = await client.post(
        "/api/v1/checkout/summary",
        json={"coupon_code": "FREE100"},
        headers=auth_headers_customer,
    )
    assert summary_res.status_code == 200
    assert summary_res.json()["is_zero_total"] is True
    assert summary_res.json()["total"] == 0.0

    # 2. Intent should safely report is_zero_total without Stripe error
    intent_res = await client.post(
        "/api/v1/checkout/create-intent",
        json={"coupon_code": "FREE100"},
        headers=auth_headers_customer,
    )
    assert intent_res.status_code == 200
    assert intent_res.json()["is_zero_total"] is True
    assert intent_res.json()["client_secret"] is None

    # 3. Direct zero-total completion creates paid order
    order_res = await client.post(
        "/api/v1/checkout/zero-total-order",
        json={"coupon_code": "FREE100"},
        headers=auth_headers_customer,
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["status"] == "paid"
    assert order_data["payment_status"] == "succeeded"
    assert order_data["total_amount"] == 0.0
