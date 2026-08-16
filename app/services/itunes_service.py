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
        if not artist_name or not track_title:
            return None

        clean_artist = self._normalize(artist_name)
        clean_title = self._normalize(track_title)
        query = f"{artist_name} {track_title}"

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
                    return None

                # Find best match
                for item in results:
                    item_artist = self._normalize(item.get("artistName", ""))
                    item_track = self._normalize(item.get("trackName", ""))
                    preview_url = item.get("previewUrl")

                    # Check if artist or track matches reasonably
                    if (clean_title in item_track or item_track in clean_title) and preview_url:
                        return preview_url

                # If no strict match, fallback to the top result's preview if available
                first_preview = results[0].get("previewUrl")
                return first_preview

        except Exception as e:
            logger.warning(f"iTunes search failed for '{artist_name} - {track_title}': {e}")
            return None
