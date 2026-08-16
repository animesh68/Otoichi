import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.models.catalog import Album, Artist, Track
from app.db.models.order import Order, OrderItem
from app.db.models.product import VinylProduct
from app.db.models.social_and_promo import (
    Coupon,
    Review,
    StockNotification,
    StripeWebhookEvent,
    Wishlist,
)
from app.db.models.user import Address, User
from app.db.mongo import get_document_models
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def mongo_db():
    """Create in-memory mocked MongoDB database and initialize Beanie models."""
    mock_client = AsyncMongoMockClient()
    test_db = mock_client["test_otoichi"]
    models = await get_document_models()
    await init_beanie(database=test_db, document_models=models)
    yield test_db


@pytest_asyncio.fixture(scope="function")
async def client(mongo_db) -> AsyncGenerator[AsyncClient, None]:
    """Provide AsyncClient wired with in-memory test database."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def seed_data(mongo_db):
    """Seed in-memory test database with standard users, coupons, and products."""
    # 1. Users
    customer = User(
        email="customer@example.com",
        password_hash=get_password_hash("Password123!"),
        full_name="Test Customer",
        role="customer",
        is_active=True,
    )
    admin = User(
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123!"),
        full_name="Test Admin",
        role="admin",
        is_active=True,
    )

    # Address
    address = Address(
        line1="456 Record Ave",
        city="Austin",
        state="TX",
        postal_code="78701",
        country="United States",
        is_default=True,
    )
    customer.addresses.append(address)

    await customer.insert()
    await admin.insert()

    # 2. Artist, Album, Tracks, Products
    artist = Artist(name="Fleetwood Mac", spotify_artist_id="artist_fm_123")
    await artist.insert()

    album = Album(
        title="Rumours",
        artist_id=artist.id,
        artist_name=artist.name,
        release_year=1977,
        genre="Classic Rock",
        spotify_album_id="album_rumours_123",
        cover_art_url="https://example.com/rumours.jpg",
    )
    await album.insert()

    track1 = Track(
        album_id=album.id,
        artist_id=artist.id,
        title="Dreams",
        track_number=2,
        duration_ms=257000,
        spotify_track_id="track_dreams_123",
        itunes_preview_url="https://example.com/dreams.m4a",
    )
    track2 = Track(
        album_id=album.id,
        artist_id=artist.id,
        title="The Chain",
        track_number=7,
        duration_ms=268000,
        spotify_track_id="track_thechain_123",
        itunes_preview_url=None,  # Missing preview test case
    )
    await track1.insert()
    await track2.insert()

    # Standalone single
    single_artist = Artist(name="Steely Dan")
    await single_artist.insert()

    single_track = Track(
        album_id=None,
        artist_id=single_artist.id,
        title="Peg",
        duration_ms=237000,
        itunes_preview_url="https://example.com/peg.m4a",
        is_standalone_single=True,
    )
    await single_track.insert()

    # Vinyl Products
    product_album = VinylProduct(
        product_type="album",
        album_id=album.id,
        format="LP",
        vinyl_variant="standard",
        price=29.99,
        stock_quantity=10,
        sku="SKU-FM-RUMOURS-LP",
    )
    product_single = VinylProduct(
        product_type="single",
        track_id=single_track.id,
        format="7\"",
        vinyl_variant="standard",
        price=14.99,
        stock_quantity=3,  # Low stock
        sku="SKU-SD-PEG-7",
    )
    product_outofstock = VinylProduct(
        product_type="album",
        album_id=album.id,
        format="12\"",
        vinyl_variant="picture_disc",
        price=49.99,
        stock_quantity=0,  # Out of stock
        sku="SKU-FM-RUMOURS-PIC",
    )
    await product_album.insert()
    await product_single.insert()
    await product_outofstock.insert()

    # 3. Coupons
    coupon_percent = Coupon(
        code="SAVE10",
        discount_type="percent",
        value=10.0,
        usage_limit=10,
        is_active=True,
    )
    coupon_fixed = Coupon(
        code="SAVE5",
        discount_type="fixed",
        value=5.0,
        usage_limit=10,
        is_active=True,
    )
    coupon_exhausted = Coupon(
        code="EXHAUSTED",
        discount_type="fixed",
        value=5.0,
        usage_limit=1,
        times_used=1,
        is_active=True,
    )
    await coupon_percent.insert()
    await coupon_fixed.insert()
    await coupon_exhausted.insert()

    return {
        "customer": customer,
        "admin": admin,
        "address": address,
        "artist": artist,
        "album": album,
        "track1": track1,
        "track2": track2,
        "product_album": product_album,
        "product_single": product_single,
        "product_outofstock": product_outofstock,
        "coupon_percent": coupon_percent,
        "coupon_fixed": coupon_fixed,
    }


@pytest.fixture
def auth_headers_customer(seed_data):
    customer = seed_data["customer"]
    token = create_access_token(subject=str(customer.id), role=customer.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin(seed_data):
    admin = seed_data["admin"]
    token = create_access_token(subject=str(admin.id), role=admin.role)
    return {"Authorization": f"Bearer {token}"}
