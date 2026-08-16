import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ArtistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    bio: Optional[str] = None
    image_url: Optional[str] = None
    spotify_artist_id: Optional[str] = None


class ArtistCreate(ArtistBase):
    pass


class ArtistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    bio: Optional[str] = None
    image_url: Optional[str] = None
    spotify_artist_id: Optional[str] = None


class ArtistResponse(ArtistBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrackBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    album_id: Optional[uuid.UUID] = None
    artist_id: Optional[uuid.UUID] = None
    artist_name: Optional[str] = None
    track_number: Optional[int] = None
    duration_ms: Optional[int] = None
    spotify_track_id: Optional[str] = None
    itunes_preview_url: Optional[str] = None


class TrackCreate(TrackBase):
    pass


class TrackUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    album_id: Optional[uuid.UUID] = None
    artist_id: Optional[uuid.UUID] = None
    artist_name: Optional[str] = None
    track_number: Optional[int] = None
    duration_ms: Optional[int] = None
    spotify_track_id: Optional[str] = None
    itunes_preview_url: Optional[str] = None


class TrackResponse(TrackBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlbumBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist_id: uuid.UUID
    artist_name: Optional[str] = None
    release_year: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_art_url: Optional[str] = None
    spotify_album_id: Optional[str] = None
    label: Optional[str] = None


class AlbumCreate(AlbumBase):
    pass


class AlbumUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    artist_id: Optional[uuid.UUID] = None
    release_year: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_art_url: Optional[str] = None
    spotify_album_id: Optional[str] = None
    label: Optional[str] = None


class AlbumResponse(AlbumBase):
    id: uuid.UUID
    created_at: datetime
    artist: Optional[ArtistResponse] = None

    model_config = ConfigDict(from_attributes=True)


class AlbumDetailResponse(AlbumResponse):
    tracks: List[TrackResponse] = []
    products: List["ProductResponseSummary"] = []
    related_albums: List[AlbumResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductResponseSummary(BaseModel):
    id: uuid.UUID
    product_type: str
    format: str
    vinyl_variant: str
    price: float
    currency: str
    stock_quantity: int
    sku: str
    is_preorder: bool
    low_stock: bool = False

    model_config = ConfigDict(from_attributes=True)
