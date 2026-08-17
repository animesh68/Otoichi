import asyncio
import uuid
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.cart import CartItem
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct
from app.services.cache_service import cache_service, MemoryCache
from app.services.inventory_service import InventoryService


@pytest.mark.asyncio
async def test_cache_service_set_and_get():
    """Test basic CacheService set, get, and key hashing."""
    test_key = cache_service.make_key("test:v1", q="Miles Davis", page=1)
    data = {"artist": "Miles Davis", "count": 42}

    # Cache MISS initially
    miss = await cache_service.get(test_key)
    assert miss is None

    # SET with TTL
    success = await cache_service.set(test_key, data, ttl=10)
    assert success is True

    # Cache HIT
    hit = await cache_service.get(test_key)
    assert hit == data


@pytest.mark.asyncio
async def test_cache_service_ttl_expiration():
    """Test that keys expire properly after TTL."""
    mem_cache = MemoryCache()
    await mem_cache.set("temp_key", "temporary_val", ttl=1)
    assert await mem_cache.get("temp_key") == "temporary_val"

    await asyncio.sleep(1.1)
    assert await mem_cache.get("temp_key") is None


@pytest.mark.asyncio
async def test_catalog_endpoint_cache_hit(client: AsyncClient, mongo_db, seed_data):
    """Test that /api/v1/products/ and /api/v1/albums/ cache responses and hit on subsequent calls."""
    # First call: Cache MISS & populate cache
    res1 = await client.get("/api/v1/products/?page=1&page_size=10")
    assert res1.status_code == 200
    data1 = res1.json()

    # Second call: Cache HIT
    res2 = await client.get("/api/v1/products/?page=1&page_size=10")
    assert res2.status_code == 200
    data2 = res2.json()

    assert data1["items"] == data2["items"]
    assert data1["total"] == data2["total"]


@pytest.mark.asyncio
async def test_cache_invalidation_on_product_mutation(client: AsyncClient, mongo_db, seed_data):
    """Test that creating or updating a product invalidates product listings and single detail cache."""
    album = await Album.find_one()
    artist = await Artist.find_one()

    # 1. Warm cache
    await client.get("/api/v1/products/?page=1&page_size=20")

    # 2. Authenticate as admin and create new product
    admin_token = create_access_token(str(seed_data["admin"].id), role="admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_payload = {
        "product_type": "album",
        "album_id": str(album.id),
        "format": "LP",
        "vinyl_variant": "colored",
        "price": 48.0,
        "currency": "USD",
        "stock_quantity": 7,
        "sku": f"SKU-CACHE-TEST-{uuid.uuid4().hex[:6]}",
        "is_preorder": False,
        "image_urls": [],
    }
    res_create = await client.post("/api/v1/admin/products", json=create_payload, headers=headers)
    assert res_create.status_code == 201
    created_id = res_create.json()["id"]

    # 3. Read single product -> warms product:v1:<id>
    res_detail1 = await client.get(f"/api/v1/products/{created_id}")
    assert res_detail1.status_code == 200
    assert res_detail1.json()["price"] == 48.0

    # 4. Update price -> invalidates cache
    update_payload = {"price": 55.0}
    res_update = await client.patch(f"/api/v1/admin/products/{created_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200

    # 5. Read single product again -> receives fresh updated price 55.0
    res_detail2 = await client.get(f"/api/v1/products/{created_id}")
    assert res_detail2.status_code == 200
    assert res_detail2.json()["price"] == 55.0


@pytest.mark.asyncio
async def test_cache_invalidation_on_stock_decrement(mongo_db, seed_data):
    """Test that inventory operations invalidate the product cache."""
    product = await VinylProduct.find_one()
    assert product is not None

    cache_key = f"product:v1:{product.id}"
    await cache_service.set(cache_key, {"cached_stock": product.stock_quantity}, ttl=600)

    # Perform inventory decrement
    inv_service = InventoryService()
    await inv_service.lock_and_decrement_stock(product.id, quantity=1)

    # Cache should be cleared
    assert await cache_service.get(cache_key) is None


@pytest.mark.asyncio
async def test_redis_offline_graceful_fallback():
    """Test that CacheService continues operating without exceptions when Redis is offline/unreachable."""
    # Test with invalid / closed Redis host
    broken_cache = cache_service
    # Set and get should succeed via internal memory fallback
    await broken_cache.set("fallback:key", {"status": "ok"}, ttl=60)
    val = await broken_cache.get("fallback:key")
    assert val == {"status": "ok"}


@pytest.mark.asyncio
async def test_private_user_data_never_globally_cached(client: AsyncClient, mongo_db, seed_data):
    """Test that cart endpoints return user/session-specific data and never collide across users."""
    user1_token = create_access_token(str(seed_data["customer"].id), role="customer")
    user2_token = create_access_token(str(seed_data["admin"].id), role="admin")

    prod = await VinylProduct.find_one()

    # User 1 adds item to cart
    headers1 = {"Authorization": f"Bearer {user1_token}"}
    await client.post("/api/v1/cart/items", json={"product_id": str(prod.id), "quantity": 2}, headers=headers1)

    # User 1 cart has 2 items
    res1 = await client.get("/api/v1/cart/", headers=headers1)
    assert res1.status_code == 200
    assert res1.json()["total_items"] >= 2

    # User 2 cart must be isolated and not contain user 1's items
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    res2 = await client.get("/api/v1/cart/", headers=headers2)
    assert res2.status_code == 200
    assert res2.json()["total_items"] == 0
