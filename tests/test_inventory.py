import asyncio
import pytest
from httpx import AsyncClient

from app.core.exceptions import InsufficientStockException
from app.services.inventory_service import InventoryService


@pytest.mark.asyncio
async def test_inventory_decrement_and_oversell_prevention(seed_data):
    """Test concurrency-safe inventory decrement and oversell rejection."""
    inventory_service = InventoryService()
    product_single = seed_data["product_single"]  # Initial stock = 3

    # Decrement 2 units
    updated_product = await inventory_service.lock_and_decrement_stock(product_single.id, 2)
    assert updated_product.stock_quantity == 1

    # Decrement final 1 unit
    updated_product = await inventory_service.lock_and_decrement_stock(product_single.id, 1)
    assert updated_product.stock_quantity == 0

    # Attempt to decrement when exhausted -> Must raise InsufficientStockException
    with pytest.raises(InsufficientStockException):
        await inventory_service.lock_and_decrement_stock(product_single.id, 1)


@pytest.mark.asyncio
async def test_inventory_restore_on_cancellation(client: AsyncClient, seed_data, auth_headers_customer, auth_headers_admin):
    """Test that cancelling an order restores product inventory."""
    product = seed_data["product_single"]  # initial stock = 3

    # Add and order 2 units
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product.id), "quantity": 2},
        headers=auth_headers_customer,
    )
    order_res = await client.post(
        "/api/v1/checkout/direct-order",
        json={},
        headers=auth_headers_customer,
    )
    order_id = order_res.json()["id"]

    # Verify stock dropped to 1
    prod_check = await client.get(f"/api/v1/products/{product.id}")
    assert prod_check.json()["stock_quantity"] == 1

    # Cancel order via admin
    cancel_res = await client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=auth_headers_admin,
    )
    assert cancel_res.status_code == 200

    # Verify stock is restored to 3
    prod_restored = await client.get(f"/api/v1/products/{product.id}")
    assert prod_restored.json()["stock_quantity"] == 3
