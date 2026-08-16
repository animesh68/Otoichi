import asyncio
import logging
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.services.spotify_service import SpotifyService
from app.services.sync_service import SyncService
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SONGS_TO_SYNC = [
    # Image 1: Midwest Emo / Indie
    {"query": "The Summer Ends American Football", "artist": "American Football", "genre": "Midwest Emo"},
    {"query": "Watching over the Garden Wall With You For When You Can't Breathe", "artist": "For When You Can't Breathe", "genre": "Indie"},
    {"query": "Never Meant American Football", "artist": "American Football", "genre": "Midwest Emo"},
    {"query": "Words That Rhyme With Different, Etc. sports.", "artist": "sports.", "genre": "Midwest Emo"},
    {"query": "Cats Macseal", "artist": "Macseal", "genre": "Midwest Emo"},
    {"query": "Death Cup Mom Jeans.", "artist": "Mom Jeans.", "genre": "Midwest Emo"},
    {"query": "Next to You Macseal", "artist": "Macseal", "genre": "Midwest Emo"},
    {"query": "im eating a chicken sandwich empty parking lot", "artist": "empty parking lot", "genre": "Indie"},
    {"query": "little stuffed shark empty parking lot", "artist": "empty parking lot", "genre": "Indie"},
    {"query": "The Thrash Particle Modern Baseball", "artist": "Modern Baseball", "genre": "Midwest Emo"},

    # Image 2: Hyperpop / Electronic / Pop
    {"query": "BrooklynBloodPop SyKo", "artist": "SyKo", "genre": "Hyperpop"},
    {"query": "love for you LOVELI LORI", "artist": "LOVELI LORI", "genre": "Hyperpop"},
    {"query": "love for you Slowed Down LOVELI LORI", "artist": "LOVELI LORI", "genre": "Hyperpop"},
    {"query": "ecstacy SUICIDAL-IDOL", "artist": "SUICIDAL-IDOL", "genre": "Hyperpop"},
    {"query": "ecstacy super slowed SUICIDAL-IDOL", "artist": "SUICIDAL-IDOL", "genre": "Hyperpop"},
    {"query": "Track 10 Charli xcx", "artist": "Charli xcx", "genre": "Hyperpop"},
    {"query": "Airplane Mode Limbo", "artist": "Limbo", "genre": "Indie Pop"},
    {"query": "SugarCrash! ElyOtto", "artist": "ElyOtto", "genre": "Hyperpop"},
    {"query": "party 4 u Charli xcx", "artist": "Charli xcx", "genre": "Hyperpop"},
    {"query": "Speed Drive Charli xcx", "artist": "Charli xcx", "genre": "Pop"},

    # Image 3: Classic Rock / Pop / Indie
    {"query": "Pour Some Sugar On Me Def Leppard", "artist": "Def Leppard", "genre": "Rock"},
    {"query": "Lonely Together Avicii Rita Ora", "artist": "Avicii", "genre": "Electronic"},
    {"query": "I Thought I Saw Your Face Today She & Him", "artist": "She & Him", "genre": "Indie Folk"},
    {"query": "Heartbreaker Pat Benatar", "artist": "Pat Benatar", "genre": "Rock"},
    {"query": "LOVE YOU LESS Joji", "artist": "Joji", "genre": "R&B"},
    {"query": "Luxurious Gwen Stefani", "artist": "Gwen Stefani", "genre": "Pop"},
    {"query": "Dizzying Highs Tape Machines", "artist": "Tape Machines", "genre": "Pop"},
    {"query": "Headstart 2019 Heux", "artist": "Heux", "genre": "Electronic"},
    {"query": "deja vu Olivia Rodrigo", "artist": "Olivia Rodrigo", "genre": "Pop"},
    {"query": "good 4 u Olivia Rodrigo", "artist": "Olivia Rodrigo", "genre": "Pop"},
    {"query": "Take Me Home Country Roads John Denver", "artist": "John Denver", "genre": "Folk"},

    # Image 4: Desi / Indie
    {"query": "bargad", "artist": "bargad", "genre": "Indie"},
    {"query": "Rakhlo Tum Chupaake", "artist": "OAFF", "genre": "Indie"},
    {"query": "Ik Kudi", "artist": "Diljit Dosanjh", "genre": "Indie"},
    {"query": "Maharani Karun", "artist": "Karun", "genre": "Hip-Hop"},
    {"query": "Pyari Amaanat", "artist": "Pyari Amaanat", "genre": "Indie"},
]

async def sync_songs():
    await connect_to_mongo()
    spotify = SpotifyService()
    sync_service = SyncService(spotify=spotify)
    
    synced_count = 0
    for item in SONGS_TO_SYNC:
        q = item["query"]
        logger.info(f"Searching Spotify for: '{q}'...")
        res = await spotify.search(q, search_type="track")
        tracks = res.get("tracks", {}).get("items", [])
        if not tracks:
            logger.warning(f"No Spotify track found for '{q}'")
            continue
        
        sp_track = tracks[0]
        track_id = sp_track["id"]
        track_name = sp_track["name"]
        artist_name = sp_track["artists"][0]["name"] if sp_track.get("artists") else item["artist"]
        album_data = sp_track.get("album", {})
        album_name = album_data.get("name", "")
        images = album_data.get("images", [])
        cover_url = images[0]["url"] if images else None
        
        logger.info(f" -> Found Track: '{track_name}' by '{artist_name}' (Album: '{album_name}')")
        
        try:
            # Sync standalone single track & 7" vinyl product
            resp = await sync_service.sync_track_by_spotify_id(track_id, default_price=14.99, default_stock=20)
            
            # Ensure artist name is explicitly populated on Track document
            trk_doc = await Track.find_one(Track.spotify_track_id == track_id)
            if trk_doc:
                trk_doc.artist_name = artist_name
                await trk_doc.save()
                
            logger.info(f" -> Successfully synced '{track_name}' by '{artist_name}' (SKU: {resp.product_sku})")
            synced_count += 1
        except Exception as e:
            logger.error(f"Error syncing track '{track_name}': {e}")
            
    logger.info(f"\n==========================================")
    logger.info(f"SYNC COMPLETE: Synced {synced_count}/{len(SONGS_TO_SYNC)} tracks into Otoichi marketplace!")
    logger.info(f"==========================================")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(sync_songs())
