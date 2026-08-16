import asyncio
import logging
from typing import List, Optional
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.services.sync_service import SyncService
from app.services.spotify_service import SpotifyService
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("catalog_sync")

REMAINING_ITEMS = [
    {"query": "The 1975 Being Funny in a Foreign Language", "type": "album", "price": 31.99, "stock": 25},
    {"query": "The 1975 About You", "type": "track", "price": 14.99, "stock": 20},
    {"query": "The 1975 Somebody Else", "type": "track", "price": 14.99, "stock": 20},
    {"query": "The 1975 Robbers", "type": "track", "price": 14.99, "stock": 20},
    {"query": "Kanye West Graduation", "type": "album", "price": 36.99, "stock": 35},
    {"query": "The Script #3 Deluxe", "type": "album", "price": 27.99, "stock": 15},
    {"query": "Radiohead Creep", "type": "track", "price": 14.99, "stock": 20},
    {"query": "Maroon 5 V", "type": "album", "price": 29.99, "stock": 25},
    {"query": "Maroon 5 Red Pill Blues", "type": "album", "price": 29.99, "stock": 20},
    
    # Selected playlist tracks
    {"query": "Maroon 5 Payphone", "type": "track", "price": 13.99, "stock": 15},
    {"query": "Maroon 5 Sugar", "type": "track", "price": 13.99, "stock": 15},
    {"query": "Maroon 5 Maps", "type": "track", "price": 13.99, "stock": 15},
    {"query": "My Chemical Romance Welcome to the Black Parade", "type": "track", "price": 15.99, "stock": 20},
    {"query": "The Killers Mr. Brightside", "type": "track", "price": 15.99, "stock": 25},
    {"query": "blink-182 I Miss You", "type": "track", "price": 14.99, "stock": 15},
    {"query": "The Goo Goo Dolls Iris", "type": "track", "price": 14.99, "stock": 15},
    {"query": "Charli xcx party 4 u", "type": "track", "price": 12.99, "stock": 12},
    {"query": "Green Day 21 Guns", "type": "track", "price": 14.99, "stock": 20},
    {"query": "2Pac Hit 'Em Up", "type": "track", "price": 16.99, "stock": 20},
    {"query": "Paramore Still Into You", "type": "track", "price": 14.99, "stock": 15},
]


async def sync_remaining():
    logger.info("Connecting to MongoDB Atlas...")
    await connect_to_mongo()
    
    spotify = SpotifyService()
    sync_service = SyncService()
    
    for item in REMAINING_ITEMS:
        query = item["query"]
        expected_type = item["type"]
        price = item["price"]
        stock = item["stock"]
        
        logger.info(f"Searching Spotify for '{query}' (type: {expected_type})...")
        try:
            search_res = await spotify.search(query, search_type=expected_type)
            if not search_res:
                logger.warning(f"No Spotify results found for '{query}'")
                continue
                
            if expected_type == "album":
                albums = search_res.get("albums", {}).get("items", [])
                if albums:
                    album_id = albums[0]["id"]
                    album_name = albums[0]["name"]
                    logger.info(f"Found Spotify Album: {album_name} (ID: {album_id}). Syncing...")
                    await sync_service.sync_album_by_spotify_id(
                        spotify_album_id=album_id,
                        default_price=price,
                        default_stock=stock,
                    )
            else:
                tracks = search_res.get("tracks", {}).get("items", [])
                if tracks:
                    track_id = tracks[0]["id"]
                    track_name = tracks[0]["name"]
                    logger.info(f"Found Spotify Track: {track_name} (ID: {track_id}). Syncing...")
                    await sync_service.sync_track_by_spotify_id(
                        spotify_track_id=track_id,
                        default_price=price,
                        default_stock=stock,
                    )
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Error syncing '{query}': {e}")
            
    logger.info("Remaining sync completed!")
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(sync_remaining())
