import pytest
from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.core.security import generate_unsubscribe_token, verify_unsubscribe_token
from app.db.models.catalog import Album, Artist, Track
from app.db.models.newsletter import NewsletterCampaign, NewsletterSubscriber
from app.db.models.product import VinylProduct
from app.services.newsletter_service import newsletter_service


@pytest.mark.asyncio
async def test_newsletter_subscribe_success(client, mongo_db):
    """Test successful newsletter subscription."""
    payload = {
        "email": "collector@example.com",
        "first_name": "Kenji",
    }
    response = await client.post("/api/v1/newsletter/subscribe", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "collector@example.com"
    assert data["first_name"] == "Kenji"
    assert data["status"] == "subscribed"

    # Verify stored in database
    sub = await NewsletterSubscriber.find_one(NewsletterSubscriber.email == "collector@example.com")
    assert sub is not None
    assert sub.status == "subscribed"
    assert sub.first_name == "Kenji"


@pytest.mark.asyncio
async def test_newsletter_subscribe_invalid_email(client):
    """Test subscription with invalid email format is rejected."""
    payload = {"email": "invalid-email-address"}
    response = await client.post("/api/v1/newsletter/subscribe", json=payload)
    assert response.status_code == 422 or response.status_code == 400


@pytest.mark.asyncio
async def test_newsletter_subscribe_duplicate_idempotent(client, mongo_db):
    """Test duplicate subscription returns success without creating duplicate DB documents."""
    payload = {"email": "listener@example.com", "first_name": "Yuki"}
    res1 = await client.post("/api/v1/newsletter/subscribe", json=payload)
    assert res1.status_code == 200

    # Repeat subscription with different name casing
    payload2 = {"email": "LISTENER@EXAMPLE.COM", "first_name": "Yuki Tanaka"}
    res2 = await client.post("/api/v1/newsletter/subscribe", json=payload2)
    assert res2.status_code == 200

    # Verify only 1 record exists in DB
    count = await NewsletterSubscriber.find(NewsletterSubscriber.email == "listener@example.com").count()
    assert count == 1


@pytest.mark.asyncio
async def test_newsletter_unsubscribe_signed_token(client, mongo_db):
    """Test unsubscribing with a valid signed token."""
    email = "audiophile@example.com"
    # Create active subscriber
    sub = NewsletterSubscriber(email=email, status="subscribed")
    await sub.insert()

    # Generate token
    token = generate_unsubscribe_token(email)
    assert verify_unsubscribe_token(token) == email

    # Submit unsubscribe request
    response = await client.post("/api/v1/newsletter/unsubscribe", json={"token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsubscribed"
    assert data["email"] == email

    # Verify in DB
    updated_sub = await NewsletterSubscriber.find_one(NewsletterSubscriber.email == email)
    assert updated_sub.status == "unsubscribed"
    assert updated_sub.unsubscribed_at is not None


@pytest.mark.asyncio
async def test_newsletter_unsubscribe_invalid_token(client):
    """Test unsubscribing with forged or corrupted token is rejected."""
    response = await client.post("/api/v1/newsletter/unsubscribe", json={"token": "forged_malicious_token"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UNSUBSCRIBE_TOKEN"


@pytest.mark.asyncio
async def test_weekly_product_selection_and_rotation(mongo_db):
    """Test deterministic product selection filters for active/in-stock products and avoids recent campaigns."""
    # 1. Create artist and albums
    artist = Artist(name="Miles Davis")
    await artist.insert()

    album1 = Album(
        title="Kind of Blue",
        artist_id=artist.id,
        artist_name="Miles Davis",
        genre="Jazz",
        cover_art_url="https://images.example.com/kind_of_blue.jpg",
        description="Masterpiece of modal jazz.",
    )
    await album1.insert()

    album2 = Album(
        title="Bitches Brew",
        artist_id=artist.id,
        artist_name="Miles Davis",
        genre="Jazz Fusion",
        cover_art_url="https://images.example.com/bitches_brew.jpg",
        description="Revolutionary electric jazz.",
    )
    await album2.insert()

    # 2. Create products
    prod1 = VinylProduct(
        product_type="album",
        album_id=album1.id,
        format="LP",
        vinyl_variant="standard",
        price=34.99,
        sku="SKU-JAZZ-001",
        stock_quantity=10,
    )
    await prod1.insert()

    prod2 = VinylProduct(
        product_type="album",
        album_id=album2.id,
        format="LP",
        vinyl_variant="standard",
        price=39.99,
        sku="SKU-JAZZ-002",
        stock_quantity=5,
    )
    await prod2.insert()

    # Initially, selects highest scored product
    selected1 = await newsletter_service.select_weekly_featured_product()
    assert selected1.id in (prod1.id, prod2.id)

    # Record campaign featuring selected1
    campaign = NewsletterCampaign(
        campaign_date="2026-W30",
        featured_product_id=selected1.id,
        subject="Issue 1",
        status="sent",
    )
    await campaign.insert()

    # Next selection should rotate to the other product
    selected2 = await newsletter_service.select_weekly_featured_product()
    expected_other = prod2.id if selected1.id == prod1.id else prod1.id
    assert selected2.id == expected_other


@pytest.mark.asyncio
async def test_weekly_campaign_execution_and_idempotency(mongo_db, seed_data):
    """Test full weekly campaign execution and duplicate prevention."""
    # Add subscribers
    sub1 = NewsletterSubscriber(email="sub1@example.com", status="subscribed")
    sub2 = NewsletterSubscriber(email="sub2@example.com", status="subscribed")
    sub_unsub = NewsletterSubscriber(email="unsub@example.com", status="unsubscribed")
    await sub1.insert()
    await sub2.insert()
    await sub_unsub.insert()

    week_id = "2026-W34-TEST"

    # First execution
    result = await newsletter_service.execute_weekly_campaign(campaign_date=week_id)
    assert result["status"] == "sent"
    assert result["recipient_count"] == 2

    # Verify campaign record in DB
    campaign = await NewsletterCampaign.find_one(NewsletterCampaign.campaign_date == week_id)
    assert campaign is not None
    assert campaign.status == "sent"
    assert campaign.recipient_count == 2
    assert campaign.sent_at is not None

    # Second execution on same week -> must be idempotent and return already_sent
    repeat_result = await newsletter_service.execute_weekly_campaign(campaign_date=week_id)
    assert repeat_result["status"] == "already_sent"
    assert repeat_result["campaign_id"] == str(campaign.id)


@pytest.mark.asyncio
async def test_scheduler_endpoint_authorization(client, seed_data):
    """Test /api/v1/newsletter/trigger-weekly security authorization."""
    # 1. Unauthorized request
    res_unauth = await client.post("/api/v1/newsletter/trigger-weekly", json={})
    assert res_unauth.status_code == 401

    # 2. Authorized request with X-Cron-Secret
    headers = {"X-Cron-Secret": settings.CRON_SECRET}
    res_auth = await client.post("/api/v1/newsletter/trigger-weekly", json={"campaign_date": "2026-W35-CRON"}, headers=headers)
    assert res_auth.status_code == 200
    assert res_auth.json()["status"] in ("sent", "already_sent")


@pytest.mark.asyncio
async def test_admin_newsletter_metrics_and_subscribers(client, seed_data):
    """Test admin endpoints for newsletter metrics and subscriber visibility."""
    # 1. Create subscribers
    await NewsletterSubscriber(email="admin_sub1@example.com", status="subscribed").insert()
    await NewsletterSubscriber(email="admin_sub2@example.com", status="unsubscribed").insert()

    # 2. Authenticate as admin
    from app.core.security import create_access_token
    admin_user = seed_data["admin"]
    customer_user = seed_data["customer"]
    admin_token = create_access_token(str(admin_user.id), role="admin")
    customer_token = create_access_token(str(customer_user.id), role="customer")

    # 3. Customer forbidden
    res_cust = await client.get("/api/v1/admin/newsletter/metrics", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_cust.status_code == 403

    # 4. Admin authorized
    res_admin = await client.get("/api/v1/admin/newsletter/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert data["total_subscribers"] >= 2
    assert data["active_subscribers"] >= 1
    assert data["unsubscribed_count"] >= 1

    # 5. Admin get subscribers list
    res_subs = await client.get("/api/v1/admin/newsletter/subscribers", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_subs.status_code == 200
    assert "items" in res_subs.json()

