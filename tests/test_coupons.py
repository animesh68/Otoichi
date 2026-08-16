import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validate_percentage_coupon(client: AsyncClient, seed_data):
    """Test percentage coupon validation."""
    res = await client.post(
        "/api/v1/coupons/validate",
        json={"code": "SAVE10", "subtotal": 100.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["discount_amount"] == 10.0


@pytest.mark.asyncio
async def test_validate_fixed_coupon(client: AsyncClient, seed_data):
    """Test fixed discount coupon validation."""
    res = await client.post(
        "/api/v1/coupons/validate",
        json={"code": "SAVE5", "subtotal": 50.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["discount_amount"] == 5.0


@pytest.mark.asyncio
async def test_coupon_discount_never_exceeds_subtotal(client: AsyncClient, seed_data):
    """Test that fixed coupon on small subtotal does not produce negative total."""
    res = await client.post(
        "/api/v1/coupons/validate",
        json={"code": "SAVE5", "subtotal": 3.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["discount_amount"] == 3.0  # Capped at subtotal


@pytest.mark.asyncio
async def test_validate_exhausted_coupon(client: AsyncClient, seed_data):
    """Test that exhausted usage limit coupon is invalid."""
    res = await client.post(
        "/api/v1/coupons/validate",
        json={"code": "EXHAUSTED", "subtotal": 100.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert "limit" in data["message"].lower()


@pytest.mark.asyncio
async def test_admin_coupon_crud(client: AsyncClient, auth_headers_admin):
    """Test admin coupon creation and management."""
    # Create
    create_res = await client.post(
        "/api/v1/coupons/",
        json={
            "code": "SUMMER25",
            "discount_type": "percent",
            "value": 25.0,
            "usage_limit": 50,
        },
        headers=auth_headers_admin,
    )
    assert create_res.status_code == 201
    coupon_id = create_res.json()["id"]

    # List
    list_res = await client.get("/api/v1/coupons/", headers=auth_headers_admin)
    assert list_res.status_code == 200
    assert any(c["code"] == "SUMMER25" for c in list_res.json())

    # Delete
    del_res = await client.delete(f"/api/v1/coupons/{coupon_id}", headers=auth_headers_admin)
    assert del_res.status_code == 200
