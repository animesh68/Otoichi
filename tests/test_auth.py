import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, seed_data):
    """Test new user registration."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Password123!",
            "full_name": "New Vinyl Lover",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New Vinyl Lover"
    assert data["role"] == "customer"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, seed_data):
    """Test duplicate registration returns 409 conflict."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer@example.com",
            "password": "Password123!",
            "full_name": "Duplicate User",
        },
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_data):
    """Test user login returns access and refresh tokens."""
    res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "customer@example.com",
            "password": "Password123!",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, seed_data):
    """Test login with wrong password returns 401."""
    res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "customer@example.com",
            "password": "WrongPassword!",
        },
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient, auth_headers_customer):
    """Test /auth/me returns authenticated customer profile."""
    res = await client.get("/api/v1/auth/me", headers=auth_headers_customer)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "customer@example.com"
    assert data["role"] == "customer"


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, seed_data):
    """Test refresh token generates a new valid access token."""
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "customer@example.com", "password": "Password123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_admin_authorization(client: AsyncClient, auth_headers_customer, auth_headers_admin):
    """Test that customer cannot access admin endpoints, but admin can."""
    # Customer forbidden
    res_customer = await client.get("/api/v1/admin/metrics", headers=auth_headers_customer)
    assert res_customer.status_code == 403

    # Admin allowed
    res_admin = await client.get("/api/v1/admin/metrics", headers=auth_headers_admin)
    assert res_admin.status_code == 200
    assert "total_users" in res_admin.json()
