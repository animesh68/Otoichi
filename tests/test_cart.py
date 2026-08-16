import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_authenticated_cart_flow(client: AsyncClient, seed_data, auth_headers_customer):
    """Test adding item, updating quantity, and viewing cart for authenticated user."""
    product = seed_data["product_album"]

    # 1. Add item
    add_res = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=auth_headers_customer,
    )
    assert add_res.status_code == 200
    cart_data = add_res.json()
    assert cart_data["total_items"] == 2
    assert cart_data["subtotal"] == round(float(product.price) * 2, 2)
    cart_item_id = cart_data["items"][0]["id"]

    # 2. Add same product again (increments quantity)
    add_again = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 1},
        headers=auth_headers_customer,
    )
    assert add_again.status_code == 200
    assert add_again.json()["total_items"] == 3

    # 3. Update quantity
    update_res = await client.patch(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 4},
        headers=auth_headers_customer,
    )
    assert update_res.status_code == 200
    assert update_res.json()["total_items"] == 4

    # 4. Remove item
    del_res = await client.delete(
        f"/api/v1/cart/items/{cart_item_id}",
        headers=auth_headers_customer,
    )
    assert del_res.status_code == 200
    assert del_res.json()["total_items"] == 0


@pytest.mark.asyncio
async def test_add_insufficient_stock(client: AsyncClient, seed_data, auth_headers_customer):
    """Test that requesting more than available stock is rejected."""
    product_single = seed_data["product_single"]  # available stock = 3

    res = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product_single.id), "quantity": 10},
        headers=auth_headers_customer,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INSUFFICIENT_STOCK"


@pytest.mark.asyncio
async def test_guest_cart_and_merging(client: AsyncClient, seed_data, auth_headers_customer):
    """Test guest cart operations with X-Session-ID and merging into user cart."""
    guest_session = "guest-session-uuid-12345"
    product_album = seed_data["product_album"]
    product_single = seed_data["product_single"]

    # 1. Guest adds product to cart
    res1 = await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product_album.id), "quantity": 1},
        headers={"X-Session-ID": guest_session},
    )
    assert res1.status_code == 200
    assert res1.json()["total_items"] == 1

    # 2. Authenticated user already has single in cart
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product_single.id), "quantity": 1},
        headers=auth_headers_customer,
    )

    # 3. Merge guest cart into user cart
    merge_res = await client.post(
        "/api/v1/cart/merge",
        json={"guest_session_id": guest_session},
        headers=auth_headers_customer,
    )
    assert merge_res.status_code == 200
    merged_data = merge_res.json()
    assert merged_data["total_items"] == 2
    assert len(merged_data["items"]) == 2

    # 4. Verify guest cart is now empty
    guest_cart_check = await client.get("/api/v1/cart/", headers={"X-Session-ID": guest_session})
    assert guest_cart_check.json()["total_items"] == 0
