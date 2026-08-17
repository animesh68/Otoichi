import logging
import re
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class iTunesService:
    def __init__(self):
        self.base_url = "https://itunes.apple.com/search"

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize string for fuzzy comparison."""
        if not text:
            return ""
        # Remove parentheses content e.g. "(Remastered 2011)"
        cleaned = re.sub(r"\([^)]*\)", "", text)
        cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)
        # Remove non-alphanumeric chars
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", cleaned)
        return " ".join(cleaned.lower().split())

    async def get_preview_url(self, artist_name: str, track_title: str) -> Optional[str]:
        """
        Search iTunes Search API for a 30-second audio preview.
        Returns previewUrl if found, else None. Never crashes on missing match.
        """
        clean_artist = self._normalize(artist_name)
        clean_title = self._normalize(track_title)
        query = f"{artist_name} {track_title}"

        from app.services.cache_service import cache_service
        cache_key = cache_service.make_key("external:itunes:v1", a=clean_artist, t=clean_title)
        cached_url = await cache_service.get(cache_key)
        if cached_url is not None:
            return None if cached_url == "__none__" else cached_url

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "term": query,
                        "entity": "song",
                        "limit": 5,
                    },
                )
                if response.status_code != 200:
                    logger.warning(f"iTunes API returned status {response.status_code} for '{query}'")
                    return None

                data = response.json()
                results = data.get("results", [])
                if not results:
                    logger.info(f"No iTunes preview match for '{artist_name} - {track_title}'")
                    await cache_service.set(cache_key, "__none__", ttl=7200)
                    return None

                # Find best match
                matched_url = None
                for item in results:
                    item_artist = self._normalize(item.get("artistName", ""))
                    item_track = self._normalize(item.get("trackName", ""))
                    preview_url = item.get("previewUrl")

                    # Check if artist or track matches reasonably
                    if (clean_title in item_track or item_track in clean_title) and preview_url:
                        matched_url = preview_url
                        break

                if not matched_url and results:
                    matched_url = results[0].get("previewUrl")

                await cache_service.set(cache_key, matched_url or "__none__", ttl=7200)
                return matched_url

        except Exception as e:
            logger.warning(f"iTunes search failed for '{artist_name} - {track_title}': {e}")
            return None
