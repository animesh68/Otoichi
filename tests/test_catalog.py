import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, seed_data):
    """Test public catalog listing."""
    res = await client.get("/api/v1/products/")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_filter_products_by_genre(client: AsyncClient, seed_data):
    """Test filtering products by genre."""
    res = await client.get("/api/v1/products/?genre=Classic Rock")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["album"]["genre"] == "Classic Rock"


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, seed_data):
    """Test search query matching artist and title."""
    res = await client.get("/api/v1/products/?q=Peg")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "SKU-SD-PEG-7"


@pytest.mark.asyncio
async def test_filter_in_stock(client: AsyncClient, seed_data):
    """Test filtering for in-stock products."""
    res = await client.get("/api/v1/products/?in_stock=true")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["stock_quantity"] > 0


@pytest.mark.asyncio
async def test_derived_low_stock(client: AsyncClient, seed_data):
    """Test that low_stock is derived correctly based on stock quantity."""
    product_single = seed_data["product_single"]  # stock_quantity = 3 <= 5
    res = await client.get(f"/api/v1/products/{product_single.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["stock_quantity"] == 3
    assert data["low_stock"] is True

    product_album = seed_data["product_album"]  # stock_quantity = 10 > 5
    res_album = await client.get(f"/api/v1/products/{product_album.id}")
    assert res_album.status_code == 200
    assert res_album.json()["low_stock"] is False


@pytest.mark.asyncio
async def test_album_detail_tracklist_and_preview(client: AsyncClient, seed_data):
    """Test album detail returns full tracklist with preview URLs."""
    album = seed_data["album"]
    res = await client.get(f"/api/v1/albums/{album.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Rumours"
    assert len(data["tracks"]) == 2
    
    # Track 1 has preview
    assert data["tracks"][0]["title"] == "Dreams"
    assert data["tracks"][0]["itunes_preview_url"] == "https://example.com/dreams.m4a"

    # Track 2 has null preview without error
    assert data["tracks"][1]["title"] == "The Chain"
    assert data["tracks"][1]["itunes_preview_url"] is None
