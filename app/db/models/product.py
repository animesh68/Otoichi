from datetime import datetime, timezone
from typing import List, Optional
import uuid
from pydantic import Field
from beanie import Document, Indexed


class VinylProduct(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    product_type: str = "album"  # "album", "single"
    album_id: Optional[uuid.UUID] = Field(default=None, index=True)
    track_id: Optional[uuid.UUID] = Field(default=None, index=True)
    format: str = "LP"  # '7"', '12"', 'LP', 'EP'
    vinyl_variant: str = "standard"  # 'standard', 'colored', 'splatter', 'picture_disc'
    price: float
    currency: str = "USD"
    stock_quantity: int = 0
    sku: Indexed(str, unique=True)
    is_preorder: bool = False
    release_date: Optional[datetime] = None
    image_urls: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "vinyl_products"
