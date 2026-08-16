import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AdminSyncRequest(BaseModel):
    query: Optional[str] = None
    spotify_album_id: Optional[str] = None
    spotify_track_id: Optional[str] = None
    spotify_url: Optional[str] = None
    default_price: Optional[float] = Field(default=29.99, ge=0)
    default_stock: Optional[int] = Field(default=20, ge=0)


class AdminSyncResponse(BaseModel):
    success: bool
    imported_type: str  # "album" or "track"
    artist_name: str
    item_title: str
    tracks_imported: int
    itunes_previews_matched: int
    itunes_previews_missing: int
    product_sku: str
    message: str


class AdminMetricsResponse(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_revenue: float
    pending_orders: int
    low_stock_products: int
