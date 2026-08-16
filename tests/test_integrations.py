import pytest
from app.services.itunes_service import iTunesService
from app.services.spotify_service import SpotifyService


def test_spotify_service_url_parsing():
    """Test extracting Spotify ID and type from various URL and URI formats."""
    # Album URL
    t1, id1 = SpotifyService.extract_spotify_id("https://open.spotify.com/album/4m2880jivSbbyEGAKfITCa?si=123")
    assert t1 == "album"
    assert id1 == "4m2880jivSbbyEGAKfITCa"

    # Track URI
    t2, id2 = SpotifyService.extract_spotify_id("spotify:track:60a0Rd6pj0xtgxMYXdMVMV")
    assert t2 == "track"
    assert id2 == "60a0Rd6pj0xtgxMYXdMVMV"


def test_itunes_normalization():
    """Test text normalization for iTunes preview matching."""
    norm = iTunesService._normalize("Dreams (2004 Remaster) [Live]")
    assert norm == "dreams"

    norm2 = iTunesService._normalize("Go Your Own Way - 2004 Remaster")
    assert "go your own way" in norm2


@pytest.mark.asyncio
async def test_itunes_preview_fallback_graceful():
    """Test iTunes lookup fallback returns None without raising exceptions when no match found."""
    itunes = iTunesService()
    # Non-existent track query
    result = await itunes.get_preview_url("NonExistentArtistXYZ12345", "NonExistentSongTitle98765")
    assert result is None
