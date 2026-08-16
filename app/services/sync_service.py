import logging
import uuid
from typing import Optional

from app.core.exceptions import NotFoundException
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct
from app.schemas.admin import AdminSyncResponse
from app.services.itunes_service import iTunesService
from app.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, db=None, spotify: Optional[SpotifyService] = None, itunes: Optional[iTunesService] = None):
        self.db = db
        self.spotify = spotify or SpotifyService()
        self.itunes = itunes or iTunesService()

    async def sync_album_by_spotify_id(
        self,
        spotify_album_id: str,
        default_price: float = 29.99,
        default_stock: int = 20,
    ) -> AdminSyncResponse:
        """Fetch album from Spotify and import into database with iTunes preview URLs."""
        album_data = await self.spotify.get_album(spotify_album_id)
        if not album_data:
            raise NotFoundException(
                code="SPOTIFY_RESOURCE_NOT_FOUND",
                message=f"Could not retrieve album '{spotify_album_id}' from Spotify",
            )

        # 1. Artist metadata
        artists = album_data.get("artists", [])
        artist_name = artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
        spotify_artist_id = artists[0].get("id") if artists else None

        # Look up or create Artist
        artist = None
        if spotify_artist_id:
            artist = await Artist.find_one(Artist.spotify_artist_id == spotify_artist_id)
        if not artist:
            artist = await Artist.find_one(Artist.name == artist_name)

        if not artist:
            artist = Artist(
                name=artist_name,
                spotify_artist_id=spotify_artist_id,
            )
            await artist.insert()
        elif spotify_artist_id and not artist.spotify_artist_id:
            artist.spotify_artist_id = spotify_artist_id
            await artist.save()

        # 2. Album metadata
        album_title = album_data.get("name", "Untitled Album")
        release_date = album_data.get("release_date", "")
        release_year = int(release_date.split("-")[0]) if release_date else None
        genres = ", ".join(album_data.get("genres", [])) or None
        images = album_data.get("images", [])
        cover_art_url = images[0].get("url") if images else None
        label = album_data.get("label")

        album = await Album.find_one(Album.spotify_album_id == spotify_album_id)
        if not album:
            album = await Album.find_one(Album.title == album_title, Album.artist_id == artist.id)

        if not album:
            album = Album(
                title=album_title,
                artist_id=artist.id,
                artist_name=artist.name,
                release_year=release_year,
                genre=genres or "Rock",
                cover_art_url=cover_art_url,
                spotify_album_id=spotify_album_id,
                label=label,
            )
            await album.insert()
        else:
            album.cover_art_url = cover_art_url or album.cover_art_url
            album.spotify_album_id = spotify_album_id or album.spotify_album_id
            album.label = label or album.label
            album.artist_name = artist.name
            await album.save()

        # 3. Tracks metadata + iTunes audio previews
        tracks_data = album_data.get("tracks", {}).get("items", [])
        tracks_imported = 0
        previews_matched = 0
        previews_missing = 0

        for item in tracks_data:
            track_title = item.get("name", "Untitled Track")
            track_number = item.get("track_number")
            duration_ms = item.get("duration_ms")
            spotify_track_id = item.get("id")

            # Look up iTunes audio preview
            preview_url = await self.itunes.get_preview_url(artist_name, track_title)
            if preview_url:
                previews_matched += 1
            else:
                previews_missing += 1

            track = None
            if spotify_track_id:
                track = await Track.find_one(Track.album_id == album.id, Track.spotify_track_id == spotify_track_id)
            if not track:
                track = await Track.find_one(Track.album_id == album.id, Track.title == track_title)

            if not track:
                track = Track(
                    album_id=album.id,
                    artist_id=artist.id,
                    title=track_title,
                    track_number=track_number,
                    duration_ms=duration_ms,
                    spotify_track_id=spotify_track_id,
                    itunes_preview_url=preview_url,
                )
                await track.insert()
            else:
                track.track_number = track_number
                track.duration_ms = duration_ms
                track.spotify_track_id = spotify_track_id or track.spotify_track_id
                if preview_url and not track.itunes_preview_url:
                    track.itunes_preview_url = preview_url
                await track.save()

            tracks_imported += 1

        # 4. Vinyl Product creation (if not exists)
        product = await VinylProduct.find_one(
            VinylProduct.album_id == album.id,
            VinylProduct.product_type == "album",
        )

        sku = f"VINYL-ALBUM-{album.id.hex[:8].upper()}"
        if not product:
            product = VinylProduct(
                product_type="album",
                album_id=album.id,
                format="LP",
                vinyl_variant="standard",
                price=default_price,
                stock_quantity=default_stock,
                sku=sku,
                image_urls=[cover_art_url] if cover_art_url else [],
            )
            await product.insert()

        return AdminSyncResponse(
            success=True,
            imported_type="album",
            artist_name=artist.name,
            item_title=album.title,
            tracks_imported=tracks_imported,
            itunes_previews_matched=previews_matched,
            itunes_previews_missing=previews_missing,
            product_sku=sku,
            message=f"Successfully synchronized album '{album.title}' by {artist.name}",
        )

    async def sync_track_by_spotify_id(
        self,
        spotify_track_id: str,
        default_price: float = 14.99,
        default_stock: int = 15,
    ) -> AdminSyncResponse:
        """Fetch standalone single track from Spotify and import into database."""
        track_data = await self.spotify.get_track(spotify_track_id)
        if not track_data:
            raise NotFoundException(
                code="SPOTIFY_RESOURCE_NOT_FOUND",
                message=f"Could not retrieve track '{spotify_track_id}' from Spotify",
            )

        # 1. Artist
        artists = track_data.get("artists", [])
        artist_name = artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
        spotify_artist_id = artists[0].get("id") if artists else None

        artist = None
        if spotify_artist_id:
            artist = await Artist.find_one(Artist.spotify_artist_id == spotify_artist_id)
        if not artist:
            artist = await Artist.find_one(Artist.name == artist_name)

        if not artist:
            artist = Artist(name=artist_name, spotify_artist_id=spotify_artist_id)
            await artist.insert()

        # 2. Track (standalone single: album_id = None)
        track_title = track_data.get("name", "Untitled Track")
        duration_ms = track_data.get("duration_ms")

        # iTunes preview lookup
        preview_url = await self.itunes.get_preview_url(artist_name, track_title)

        track = await Track.find_one(Track.album_id == None, Track.spotify_track_id == spotify_track_id)
        if not track:
            track = await Track.find_one(Track.album_id == None, Track.title == track_title)

        if not track:
            track = Track(
                album_id=None,
                artist_id=artist.id,
                title=track_title,
                duration_ms=duration_ms,
                spotify_track_id=spotify_track_id,
                itunes_preview_url=preview_url,
                is_standalone_single=True,
            )
            await track.insert()
        else:
            if preview_url and not track.itunes_preview_url:
                track.itunes_preview_url = preview_url
                await track.save()

        # 3. Vinyl Product for Single
        product = await VinylProduct.find_one(
            VinylProduct.track_id == track.id,
            VinylProduct.product_type == "single",
        )

        album_images = track_data.get("album", {}).get("images", [])
        image_urls = [album_images[0]["url"]] if album_images else []

        sku = f"VINYL-SINGLE-{track.id.hex[:8].upper()}"
        if not product:
            product = VinylProduct(
                product_type="single",
                track_id=track.id,
                format="7\"",
                vinyl_variant="standard",
                price=default_price,
                stock_quantity=default_stock,
                sku=sku,
                image_urls=image_urls,
            )
            await product.insert()

        return AdminSyncResponse(
            success=True,
            imported_type="track",
            artist_name=artist.name,
            item_title=track.title,
            tracks_imported=1,
            itunes_previews_matched=1 if preview_url else 0,
            itunes_previews_missing=0 if preview_url else 1,
            product_sku=sku,
            message=f"Successfully synchronized standalone single '{track.title}' by {artist.name}",
        )
