import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_review_eligibility_enforcement(client: AsyncClient, seed_data, auth_headers_customer, auth_headers_admin):
    """
    Test review submission rules:
      - Rejected if user has not purchased product in a delivered order
      - Allowed once order reaches 'delivered'
      - Duplicate review rejected
    """
    product = seed_data["product_album"]

    # 1. Attempt to review without purchasing -> 403 Forbidden
    res1 = await client.post(
        "/api/v1/reviews/",
        json={"product_id": str(product.id), "rating": 5, "comment": "Great pressing!"},
        headers=auth_headers_customer,
    )
    assert res1.status_code == 403
    assert res1.json()["error"]["code"] == "VERIFIED_PURCHASE_REQUIRED"

    # 2. Purchase product, but order is only 'paid'
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

    # Still rejected because order status is 'paid', not 'delivered'
    res2 = await client.post(
        "/api/v1/reviews/",
        json={"product_id": str(product.id), "rating": 5, "comment": "Great pressing!"},
        headers=auth_headers_customer,
    )
    assert res2.status_code == 403

    # 3. Transition order to 'shipped' then 'delivered'
    await client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "shipped"}, headers=auth_headers_admin)
    await client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "delivered"}, headers=auth_headers_admin)

    # 4. Now review submission succeeds
    res3 = await client.post(
        "/api/v1/reviews/",
        json={"product_id": str(product.id), "rating": 5, "comment": "Authentic warm analog sound!"},
        headers=auth_headers_customer,
    )
    assert res3.status_code == 201
    assert res3.json()["rating"] == 5

    # 5. Duplicate review attempt is rejected
    res4 = await client.post(
        "/api/v1/reviews/",
        json={"product_id": str(product.id), "rating": 4, "comment": "Second review attempt"},
        headers=auth_headers_customer,
    )
    assert res4.status_code == 409
    assert res4.json()["error"]["code"] == "REVIEW_ALREADY_EXISTS"
