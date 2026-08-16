import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Query
from beanie.operators import In, Or, RegEx

from app.core.exceptions import NotFoundException
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct
from app.schemas.common import PaginatedResponse
from app.schemas.product import ProductResponse
from app.services.cart_service import build_product_response

products_router = APIRouter(prefix="/products", tags=["Vinyl Products"])


@products_router.get("/", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    q: Optional[str] = Query(None, description="Search query across albums, artists, tracks, and SKUs"),
    genre: Optional[str] = Query(None, description="Filter by music genre"),
    artist_id: Optional[uuid.UUID] = Query(None, description="Filter by artist ID"),
    album_id: Optional[uuid.UUID] = Query(None, description="Filter by album ID"),
    format: Optional[str] = Query(None, description="Filter by vinyl format (7\", 12\", LP, EP)"),
    vinyl_variant: Optional[str] = Query(None, description="Filter by vinyl variant (standard, colored, splatter, picture_disc)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by in-stock availability"),
    is_preorder: Optional[bool] = Query(None, description="Filter by preorder status"),
    sort_by: Optional[str] = Query(
        "newest",
        description="Sort by: 'newest', 'price_asc', 'price_desc', 'sku_asc'",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Search and filter sellable vinyl products with pagination and sorting.
    """
    filters = []

    if q:
        matching_albums = await Album.find(RegEx(Album.title, q.strip(), "i")).to_list()
        matching_artists = await Artist.find(RegEx(Artist.name, q.strip(), "i")).to_list()
        artist_album_ids = []
        if matching_artists:
            artist_albums = await Album.find(In(Album.artist_id, [a.id for a in matching_artists])).to_list()
            artist_album_ids = [a.id for a in artist_albums]

        album_ids = list(set([a.id for a in matching_albums] + artist_album_ids))
        matching_tracks = await Track.find(RegEx(Track.title, q.strip(), "i")).to_list()
        track_ids = [t.id for t in matching_tracks]

        filters.append(
            Or(
                RegEx(VinylProduct.sku, q.strip(), "i"),
                In(VinylProduct.album_id, album_ids) if album_ids else VinylProduct.sku == "__none__",
                In(VinylProduct.track_id, track_ids) if track_ids else VinylProduct.sku == "__none__",
            )
        )

    if genre:
        matching_albums = await Album.find(RegEx(Album.genre, genre.strip(), "i")).to_list()
        album_ids = [a.id for a in matching_albums]
        filters.append(In(VinylProduct.album_id, album_ids) if album_ids else VinylProduct.sku == "__none__")

    if artist_id:
        matching_albums = await Album.find(Album.artist_id == artist_id).to_list()
        album_ids = [a.id for a in matching_albums]
        filters.append(In(VinylProduct.album_id, album_ids) if album_ids else VinylProduct.sku == "__none__")

    if album_id:
        filters.append(VinylProduct.album_id == album_id)

    if format:
        filters.append(VinylProduct.format == format)
    if vinyl_variant:
        filters.append(VinylProduct.vinyl_variant == vinyl_variant)
    if min_price is not None:
        filters.append(VinylProduct.price >= min_price)
    if max_price is not None:
        filters.append(VinylProduct.price <= max_price)
    if in_stock is True:
        filters.append(VinylProduct.stock_quantity > 0)
    elif in_stock is False:
        filters.append(VinylProduct.stock_quantity == 0)
    if is_preorder is not None:
        filters.append(VinylProduct.is_preorder == is_preorder)

    query = VinylProduct.find(*filters) if filters else VinylProduct.find()
    total = await query.count()

    # Sorting
    if sort_by == "price_asc":
        query = query.sort(+VinylProduct.price)
    elif sort_by == "price_desc":
        query = query.sort(-VinylProduct.price)
    elif sort_by == "sku_asc":
        query = query.sort(+VinylProduct.sku)
    else:  # newest
        query = query.sort(-VinylProduct.created_at)

    products = await query.skip((page - 1) * page_size).limit(page_size).to_list()
    items = [await build_product_response(p) for p in products]

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@products_router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID):
    """Get single vinyl product details with computed derived low_stock flag."""
    product = await VinylProduct.find_one(VinylProduct.id == product_id)
    if not product:
        raise NotFoundException(code="PRODUCT_NOT_FOUND", message="Product not found")

    return await build_product_response(product)
