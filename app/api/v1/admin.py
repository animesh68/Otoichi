import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.config import settings
from app.core.dependencies import require_admin
from app.core.exceptions import BadRequestException, NotFoundException
from app.db.models.order import Order
from app.db.models.product import VinylProduct
from app.db.models.user import User
from app.schemas.admin import AdminMetricsResponse, AdminSyncRequest, AdminSyncResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.cart_service import build_product_response
from app.services.order_service import OrderService
from app.services.spotify_service import SpotifyService
from app.services.sync_service import SyncService

admin_router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@admin_router.post("/sync", response_model=AdminSyncResponse)
async def sync_catalog_item(
    req: AdminSyncRequest,
    admin: User = Depends(require_admin),
):
    """
    Synchronize album or track metadata from Spotify and iTunes preview URLs.
    Accepts Spotify Album ID, Track ID, or URL.
    """
    sync_service = SyncService()

    spotify_album_id = req.spotify_album_id
    spotify_track_id = req.spotify_track_id

    if req.spotify_url:
        parsed = SpotifyService.extract_spotify_id(req.spotify_url)
        if parsed:
            resource_type, res_id = parsed
            if resource_type == "album":
                spotify_album_id = res_id
            elif resource_type == "track":
                spotify_track_id = res_id

    if spotify_album_id:
        return await sync_service.sync_album_by_spotify_id(
            spotify_album_id=spotify_album_id,
            default_price=req.default_price or 29.99,
            default_stock=req.default_stock or 20,
        )
    elif spotify_track_id:
        return await sync_service.sync_track_by_spotify_id(
            spotify_track_id=spotify_track_id,
            default_price=req.default_price or 14.99,
            default_stock=req.default_stock or 15,
        )
    elif req.query:
        spotify = SpotifyService()
        search_res = await spotify.search(req.query)
        if not search_res:
            raise NotFoundException(message=f"No Spotify results found for query '{req.query}'")

        albums = search_res.get("albums", {}).get("items", [])
        if albums:
            return await sync_service.sync_album_by_spotify_id(
                spotify_album_id=albums[0]["id"],
                default_price=req.default_price or 29.99,
                default_stock=req.default_stock or 20,
            )
        tracks = search_res.get("tracks", {}).get("items", [])
        if tracks:
            return await sync_service.sync_track_by_spotify_id(
                spotify_track_id=tracks[0]["id"],
                default_price=req.default_price or 14.99,
                default_stock=req.default_stock or 15,
            )
        raise NotFoundException(message=f"No matching albums or tracks found for '{req.query}'")
    else:
        raise BadRequestException(message="Must provide spotify_album_id, spotify_track_id, spotify_url, or search query")


from beanie.operators import In


@admin_router.get("/metrics", response_model=AdminMetricsResponse)
async def get_admin_metrics(admin: User = Depends(require_admin)):
    """Admin dashboard overview metrics."""
    users_cnt = await User.count()
    prod_cnt = await VinylProduct.count()
    order_cnt = await Order.count()

    paid_orders = await Order.find(In(Order.status, ["paid", "shipped", "delivered"])).to_list()
    revenue_val = sum(o.total_amount for o in paid_orders)

    pending_cnt = await Order.find(Order.status == "pending").count()
    low_stock_cnt = await VinylProduct.find(VinylProduct.stock_quantity <= settings.LOW_STOCK_THRESHOLD).count()

    return AdminMetricsResponse(
        total_users=users_cnt,
        total_products=prod_cnt,
        total_orders=order_cnt,
        total_revenue=float(revenue_val),
        pending_orders=pending_cnt,
        low_stock_products=low_stock_cnt,
    )


@admin_router.get("/orders", response_model=PaginatedResponse[OrderResponse])
async def list_all_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
):
    """Admin: List all orders with status filtering and pagination."""
    query = Order.find(Order.status == status_filter) if status_filter else Order.find()
    total = await query.count()
    items = await query.sort(-Order.created_at).skip((page - 1) * page_size).limit(page_size).to_list()

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


@admin_router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: uuid.UUID,
    req: OrderStatusUpdate,
    admin: User = Depends(require_admin),
):
    """Admin: Update order status with validation against allowed state transitions."""
    order_service = OrderService()
    return await order_service.update_order_status(order_id=order_id, new_status=req.status)


# ==================== PRODUCT CRUD ====================

@admin_router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    prod_in: ProductCreate,
    admin: User = Depends(require_admin),
):
    """Admin: Manually create a vinyl product SKU."""
    product = VinylProduct(
        product_type=prod_in.product_type,
        album_id=prod_in.album_id,
        track_id=prod_in.track_id,
        format=prod_in.format,
        vinyl_variant=prod_in.vinyl_variant,
        price=prod_in.price,
        currency=prod_in.currency,
        stock_quantity=prod_in.stock_quantity,
        sku=prod_in.sku,
        is_preorder=prod_in.is_preorder,
        release_date=prod_in.release_date,
        image_urls=prod_in.image_urls,
    )
    await product.insert()
    from app.services.cache_service import cache_service
    await cache_service.invalidate_product(product.id)
    return await build_product_response(product)


@admin_router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    prod_in: ProductUpdate,
    admin: User = Depends(require_admin),
):
    """Admin: Update vinyl product."""
    product = await VinylProduct.find_one(VinylProduct.id == product_id)
    if not product:
        raise NotFoundException(code="PRODUCT_NOT_FOUND", message="Product not found")

    update_data = prod_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await product.save()
    from app.services.cache_service import cache_service
    await cache_service.invalidate_product(product_id)
    return await build_product_response(product)


@admin_router.delete("/products/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: uuid.UUID,
    admin: User = Depends(require_admin),
):
    """Admin: Delete vinyl product."""
    product = await VinylProduct.find_one(VinylProduct.id == product_id)
    if not product:
        raise NotFoundException(code="PRODUCT_NOT_FOUND", message="Product not found")

    await product.delete()
    from app.services.cache_service import cache_service
    await cache_service.invalidate_product(product_id)
    return MessageResponse(message="Product deleted successfully")


# ==================== CACHE TELEMETRY ====================

@admin_router.get("/cache/metrics")
async def get_cache_metrics(
    admin: User = Depends(require_admin),
):
    """Admin: View real-time Redis/Memory cache telemetry and hit ratios."""
    from app.services.cache_service import cache_service
    return cache_service.get_metrics()


@admin_router.post("/cache/flush", response_model=MessageResponse)
async def flush_cache(
    admin: User = Depends(require_admin),
):
    """Admin: Invalidate all cached data."""
    from app.services.cache_service import cache_service
    await cache_service.delete_pattern("*")
    return MessageResponse(message="Cache flushed successfully")


# --- Newsletter Admin Operations ---

@admin_router.get("/newsletter/metrics")
async def get_newsletter_metrics(
    admin: User = Depends(require_admin),
):
    """Admin: View newsletter subscriber counts and campaign status."""
    from app.db.models.newsletter import NewsletterCampaign, NewsletterSubscriber

    total_subscribers = await NewsletterSubscriber.count()
    active_subscribers = await NewsletterSubscriber.find(NewsletterSubscriber.status == "subscribed").count()
    unsubscribed_count = await NewsletterSubscriber.find(NewsletterSubscriber.status == "unsubscribed").count()
    total_campaigns_sent = await NewsletterCampaign.find(NewsletterCampaign.status == "sent").count()
    
    latest_campaign = (
        await NewsletterCampaign.find()
        .sort("-created_at")
        .first_or_none()
    )

    return {
        "total_subscribers": total_subscribers,
        "active_subscribers": active_subscribers,
        "unsubscribed_count": unsubscribed_count,
        "total_campaigns_sent": total_campaigns_sent,
        "latest_campaign": latest_campaign,
    }


@admin_router.get("/newsletter/subscribers")
async def get_newsletter_subscribers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(require_admin),
):
    """Admin: List newsletter subscribers with pagination."""
    from app.db.models.newsletter import NewsletterSubscriber

    query = {}
    if status_filter:
        query["status"] = status_filter

    total = await NewsletterSubscriber.find(query).count()
    skip = (page - 1) * page_size
    subscribers = await NewsletterSubscriber.find(query).sort("-created_at").skip(skip).limit(page_size).to_list()

    return {
        "items": subscribers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if page_size else 1,
    }


@admin_router.get("/newsletter/campaigns")
async def get_newsletter_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    admin: User = Depends(require_admin),
):
    """Admin: List weekly campaign dispatch history."""
    from app.db.models.newsletter import NewsletterCampaign

    total = await NewsletterCampaign.count()
    skip = (page - 1) * page_size
    campaigns = await NewsletterCampaign.find().sort("-created_at").skip(skip).limit(page_size).to_list()

    return {
        "items": campaigns,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if page_size else 1,
    }


@admin_router.post("/newsletter/trigger")
async def admin_trigger_newsletter(
    campaign_date: Optional[str] = None,
    force_retry: bool = False,
    admin: User = Depends(require_admin),
):
    """Admin: Manually trigger or test weekly newsletter dispatch."""
    from app.services.newsletter_service import newsletter_service

    return await newsletter_service.execute_weekly_campaign(
        campaign_date=campaign_date,
        force_retry=force_retry,
    )

