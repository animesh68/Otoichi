import base64
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpotifyService:
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> Optional[str]:
        """Obtain or reuse cached Spotify API token using Client Credentials flow."""
        if not self.client_id or not self.client_secret:
            logger.warning("Spotify credentials not configured; Spotify API lookups will be mocked/skipped.")
            return None

        now = datetime.now(timezone.utc)
        if self._access_token and self._token_expires_at and now < self._token_expires_at:
            return self._access_token

        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://accounts.spotify.com/api/token",
                    data={"grant_type": "client_credentials"},
                    headers={"Authorization": f"Basic {auth_header}"},
                )
                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = datetime.fromtimestamp(
                        now.timestamp() + expires_in - 60, tz=timezone.utc
                    )
                    return self._access_token
                else:
                    logger.error(f"Spotify token request failed with status {response.status_code}: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Spotify token: {e}")
            return None

    async def get_album(self, spotify_album_id: str) -> Optional[Dict[str, Any]]:
        """Fetch album metadata and complete tracklist by Spotify album ID."""
        token = await self._get_access_token()
        if not token:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/albums/{spotify_album_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Spotify get_album failed for {spotify_album_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error requesting album {spotify_album_id} from Spotify: {e}")
            return None

    async def get_track(self, spotify_track_id: str) -> Optional[Dict[str, Any]]:
        """Fetch track metadata by Spotify track ID."""
        token = await self._get_access_token()
        if not token:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.spotify.com/v1/tracks/{spotify_track_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Spotify get_track failed for {spotify_track_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error requesting track {spotify_track_id} from Spotify: {e}")
            return None

    async def search(self, query: str, search_type: str = "album,track") -> Optional[Dict[str, Any]]:
        """Search Spotify catalog for albums and tracks."""
        token = await self._get_access_token()
        if not token:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": query, "type": search_type, "limit": 5},
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Spotify search failed for query '{query}': {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error searching Spotify for '{query}': {e}")
            return None

    @staticmethod
    def extract_spotify_id(uri_or_url: str) -> Optional[tuple[str, str]]:
        """
        Extract resource type ('album' or 'track') and Spotify ID from a URL or URI.
        Examples:
          https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa -> ('album', '4m2880jivSbbyEGAKfITCa')
          spotify:track:60a0Rd6pj0xtgxMYXdMVMV -> ('track', '60a0Rd6pj0xtgxMYXdMVMV')
        """
        if not uri_or_url:
            return None

        cleaned = uri_or_url.strip()
        if "spotify.com" in cleaned:
            parts = cleaned.split("spotify.com/")[1].split("?")[0].split("/")
            if len(parts) >= 2 and parts[0] in ("album", "track", "artist"):
                return parts[0], parts[1]
        elif cleaned.startswith("spotify:"):
            parts = cleaned.split(":")
            if len(parts) >= 3 and parts[1] in ("album", "track", "artist"):
                return parts[1], parts[2]

        return None
