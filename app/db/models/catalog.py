from datetime import datetime, timezone
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from beanie import Document, Indexed


class Track(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    album_id: Optional[uuid.UUID] = Field(default=None, index=True)
    artist_id: Optional[uuid.UUID] = Field(default=None, index=True)
    artist_name: Optional[str] = None
    title: str
    track_number: Optional[int] = None
    duration_ms: Optional[int] = None
    spotify_track_id: Optional[str] = Field(default=None, index=True)
    itunes_preview_url: Optional[str] = None
    is_standalone_single: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tracks"


class Album(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    artist_id: uuid.UUID = Field(index=True)
    artist_name: Optional[str] = None
    release_year: Optional[int] = None
    genre: str = Field(index=True)
    description: Optional[str] = None
    cover_art_url: Optional[str] = None
    spotify_album_id: Optional[str] = Field(default=None, index=True)
    label: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "albums"


class Artist(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: Indexed(str)
    bio: Optional[str] = None
    image_url: Optional[str] = None
    spotify_artist_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "artists"
