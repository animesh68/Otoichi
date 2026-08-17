import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Query
from beanie.operators import Or, RegEx

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct
from app.schemas.catalog import (
    AlbumDetailResponse,
    AlbumResponse,
    ArtistResponse,
    ProductResponseSummary,
    TrackResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.cache_service import cache_service

artists_router = APIRouter(prefix="/artists", tags=["Artists"])
albums_router = APIRouter(prefix="/albums", tags=["Albums"])
tracks_router = APIRouter(prefix="/tracks", tags=["Tracks"])


# ==================== ARTISTS ====================

@artists_router.get("/", response_model=PaginatedResponse[ArtistResponse])
async def list_artists(
    q: Optional[str] = Query(None, description="Search artist name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List artists with search and pagination (Cached for 30m)."""
    cache_key = cache_service.make_key("artists:v1", q=q, page=page, page_size=page_size)
    cached = await cache_service.get(cache_key)
    if cached:
        return PaginatedResponse[ArtistResponse](**cached)

    query = Artist.find()
    if q:
        query = Artist.find(RegEx(Artist.name, q.strip(), "i"))

    total = await query.count()
    items = await query.sort(+Artist.name).skip((page - 1) * page_size).limit(page_size).to_list()

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    response = PaginatedResponse(
        items=[ArtistResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    await cache_service.set(cache_key, response, ttl=1800)
    return response


@artists_router.get("/{artist_id}", response_model=ArtistResponse)
async def get_artist(artist_id: uuid.UUID):
    """Get artist details by ID (Cached for 30m)."""
    cache_key = f"artist:v1:{artist_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return ArtistResponse(**cached)

    artist = await Artist.find_one(Artist.id == artist_id)
    if not artist:
        raise NotFoundException(code="ARTIST_NOT_FOUND", message="Artist not found")

    response = ArtistResponse.model_validate(artist)
    await cache_service.set(cache_key, response, ttl=1800)
    return response


# ==================== ALBUMS ====================

from beanie.operators import In, Or, RegEx

@albums_router.get("/", response_model=PaginatedResponse[AlbumResponse])
async def list_albums(
    q: Optional[str] = Query(None, description="Search album title or artist"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    artist_id: Optional[uuid.UUID] = Query(None, description="Filter by artist ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List albums with genre filtering, search, and pagination (Cached for 10m)."""
    cache_key = cache_service.make_key(
        "albums:v1",
        q=q,
        genre=genre,
        artist_id=artist_id,
        page=page,
        page_size=page_size,
    )
    cached = await cache_service.get(cache_key)
    if cached:
        return PaginatedResponse[AlbumResponse](**cached)

    filters = []
    if q:
        matching_artists = await Artist.find(RegEx(Artist.name, q.strip(), "i")).to_list()
        artist_ids = [a.id for a in matching_artists]
        filters.append(
            Or(
                RegEx(Album.title, q.strip(), "i"),
                RegEx(Album.artist_name, q.strip(), "i"),
                In(Album.artist_id, artist_ids) if artist_ids else Album.title == "__none__",
            )
        )
    if genre:
        filters.append(RegEx(Album.genre, genre.strip(), "i"))
    if artist_id:
        filters.append(Album.artist_id == artist_id)

    query = Album.find(*filters) if filters else Album.find()
    total = await query.count()
    albums = await query.sort(-Album.release_year, +Album.title).skip((page - 1) * page_size).limit(page_size).to_list()

    album_ids = [alb.id for alb in albums]
    artist_ids = list({alb.artist_id for alb in albums if alb.artist_id})

    # Batch fetch artists and tracks
    artists = await Artist.find(In(Artist.id, artist_ids)).to_list() if artist_ids else []
    artist_map = {a.id: a for a in artists}

    tracks = (
        await Track.find(In(Track.album_id, album_ids)).sort(+Track.track_number).to_list()
        if album_ids
        else []
    )
    tracks_by_album: dict[uuid.UUID, list] = {}
    for t in tracks:
        if t.album_id:
            tracks_by_album.setdefault(t.album_id, []).append(t)

    items = []
    for alb in albums:
        artist = artist_map.get(alb.artist_id)
        artist_resp = ArtistResponse.model_validate(artist) if artist else None
        alb_tracks = tracks_by_album.get(alb.id, [])
        items.append(
            AlbumResponse(
                id=alb.id,
                title=alb.title,
                artist_id=alb.artist_id,
                artist_name=artist.name if artist else alb.artist_name,
                release_year=alb.release_year,
                genre=alb.genre,
                description=alb.description,
                cover_art_url=alb.cover_art_url,
                spotify_album_id=alb.spotify_album_id,
                label=alb.label,
                created_at=alb.created_at,
                artist=artist_resp,
                tracks=[TrackResponse.model_validate(t) for t in alb_tracks],
            )
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    response = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    await cache_service.set(cache_key, response, ttl=600)
    return response


@albums_router.get("/{album_id}", response_model=AlbumDetailResponse)
async def get_album_details(album_id: uuid.UUID):
    """
    Get full album details (Cached for 15m).
    """
    cache_key = f"album:v1:{album_id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return AlbumDetailResponse(**cached)

    album = await Album.find_one(Album.id == album_id)
    if not album:
        raise NotFoundException(code="ALBUM_NOT_FOUND", message="Album not found")

    artist = await Artist.find_one(Artist.id == album.artist_id)
    artist_resp = ArtistResponse.model_validate(artist) if artist else None

    tracks = await Track.find(Track.album_id == album.id).sort(+Track.track_number).to_list()
    products = await VinylProduct.find(VinylProduct.album_id == album.id).to_list()

    # Fetch related albums
    related_docs = await Album.find(
        Album.id != album.id,
        Or(Album.artist_id == album.artist_id, Album.genre == album.genre),
    ).limit(6).to_list()

    rel_artist_ids = list({rel.artist_id for rel in related_docs if rel.artist_id})
    rel_artists = await Artist.find(In(Artist.id, rel_artist_ids)).to_list() if rel_artist_ids else []
    rel_artist_map = {a.id: a for a in rel_artists}

    related_albums = []
    for rel in related_docs:
        rel_artist = rel_artist_map.get(rel.artist_id)
        related_albums.append(
            AlbumResponse(
                id=rel.id,
                title=rel.title,
                artist_id=rel.artist_id,
                artist_name=rel_artist.name if rel_artist else rel.artist_name,
                release_year=rel.release_year,
                genre=rel.genre,
                description=rel.description,
                cover_art_url=rel.cover_art_url,
                spotify_album_id=rel.spotify_album_id,
                label=rel.label,
                created_at=rel.created_at,
                artist=ArtistResponse.model_validate(rel_artist) if rel_artist else None,
                tracks=[],
            )
        )

    products_summary = [
        ProductResponseSummary(
            id=p.id,
            product_type=p.product_type,
            format=p.format,
            vinyl_variant=p.vinyl_variant,
            price=float(p.price),
            currency=p.currency,
            stock_quantity=p.stock_quantity,
            sku=p.sku,
            is_preorder=p.is_preorder,
            low_stock=p.stock_quantity <= settings.LOW_STOCK_THRESHOLD,
        )
        for p in products
    ]

    response = AlbumDetailResponse(
        id=album.id,
        title=album.title,
        artist_id=album.artist_id,
        release_year=album.release_year,
        genre=album.genre,
        description=album.description,
        cover_art_url=album.cover_art_url,
        spotify_album_id=album.spotify_album_id,
        label=album.label,
        created_at=album.created_at,
        artist=artist_resp,
        tracks=[TrackResponse.model_validate(t) for t in tracks],
        products=products_summary,
        related_albums=related_albums,
    )
    await cache_service.set(cache_key, response, ttl=900)
    return response


# ==================== TRACKS ====================

@tracks_router.get("/", response_model=PaginatedResponse[TrackResponse])
async def list_tracks(
    q: Optional[str] = Query(None, description="Search track title"),
    album_id: Optional[uuid.UUID] = Query(None, description="Filter by album ID"),
    standalone_only: bool = Query(False, description="List only standalone singles"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List tracks / standalone singles."""
    filters = []
    if q:
        filters.append(RegEx(Track.title, q.strip(), "i"))
    if album_id:
        filters.append(Track.album_id == album_id)
    if standalone_only:
        filters.append(Track.album_id == None)

    query = Track.find(*filters) if filters else Track.find()
    total = await query.count()
    tracks = await query.sort(+Track.title).skip((page - 1) * page_size).limit(page_size).to_list()

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        items=[TrackResponse.model_validate(t) for t in tracks],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@tracks_router.get("/{track_id}", response_model=TrackResponse)
async def get_track(track_id: uuid.UUID):
    """Get track by ID."""
    track = await Track.find_one(Track.id == track_id)
    if not track:
        raise NotFoundException(code="TRACK_NOT_FOUND", message="Track not found")
    return track
