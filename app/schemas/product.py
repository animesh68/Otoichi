import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.config import settings
from app.schemas.catalog import AlbumResponse, TrackResponse


class ProductBase(BaseModel):
    product_type: str = Field(default="album", pattern="^(album|single)$")
    album_id: Optional[uuid.UUID] = None
    track_id: Optional[uuid.UUID] = None
    format: str = Field(default="LP", pattern="^(7\"|12\"|LP|EP)$")
    vinyl_variant: str = Field(default="standard", pattern="^(standard|colored|splatter|picture_disc)$")
    price: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=10)
    stock_quantity: int = Field(default=0, ge=0)
    sku: str = Field(..., min_length=1, max_length=100)
    is_preorder: bool = False
    release_date: Optional[datetime] = None
    image_urls: List[str] = Field(default_factory=list)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_type: Optional[str] = Field(None, pattern="^(album|single)$")
    album_id: Optional[uuid.UUID] = None
    track_id: Optional[uuid.UUID] = None
    format: Optional[str] = Field(None, pattern="^(7\"|12\"|LP|EP)$")
    vinyl_variant: Optional[str] = Field(None, pattern="^(standard|colored|splatter|picture_disc)$")
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    is_preorder: Optional[bool] = None
    release_date: Optional[datetime] = None
    image_urls: Optional[List[str]] = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    album: Optional[AlbumResponse] = None
    track: Optional[TrackResponse] = None

    @computed_field
    def low_stock(self) -> bool:
        """Derived field: True if in stock but below threshold."""
        return self.stock_quantity <= settings.LOW_STOCK_THRESHOLD

    model_config = ConfigDict(from_attributes=True)
