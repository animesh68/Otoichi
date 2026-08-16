import asyncio
import logging
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.services.sync_service import SyncService
from app.services.spotify_service import SpotifyService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("extra_sync")

ITEMS = [
    {"query": "Red Pill Blues Maroon 5", "type": "album", "price": 29.99, "stock": 20},
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
    {"query": "Bullet For My Valentine Tears Don't Fall", "type": "track", "price": 14.99, "stock": 15},
    {"query": "Breaking Benjamin The Diary of Jane", "type": "track", "price": 14.99, "stock": 15},
    {"query": "Three Days Grace I Hate Everything About You", "type": "track", "price": 14.99, "stock": 15},
]


async def run():
    await connect_to_mongo()
    spotify = SpotifyService()
    sync = SyncService()
    
    for it in ITEMS:
        q = it["query"]
        t = it["type"]
        price = it["price"]
        stock = it["stock"]
        
        logger.info(f"Syncing: {q} ({t})")
        search_res = await spotify.search(q, search_type=t)
        if not search_res:
            continue
            
        if t == "album":
            albums = search_res.get("albums", {}).get("items", [])
            if albums:
                alb = albums[0]
                logger.info(f"Adding Album: {alb['name']} ({alb['id']})")
                await sync.sync_album_by_spotify_id(alb["id"], default_price=price, default_stock=stock)
        else:
            tracks = search_res.get("tracks", {}).get("items", [])
            if tracks:
                trk = tracks[0]
                logger.info(f"Adding Single SKU: {trk['name']} ({trk['id']})")
                await sync.sync_track_by_spotify_id(trk["id"], default_price=price, default_stock=stock)
                
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run())
