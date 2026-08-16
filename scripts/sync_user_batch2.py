import asyncio
import logging
from typing import List, Dict, Any
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.services.sync_service import SyncService
from app.services.spotify_service import SpotifyService
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_batch2")

BATCH_ITEMS = [
    # Maroon 5 Albums & Tracks
    {"query": "Songs About Jane Maroon 5", "type": "album", "price": 31.99, "stock": 25},
    {"query": "Overexposed Maroon 5", "type": "album", "price": 28.99, "stock": 20},
    {"query": "Hands All Over Maroon 5", "type": "album", "price": 27.99, "stock": 20},
    {"query": "JORDI Maroon 5", "type": "album", "price": 26.99, "stock": 15},
    {"query": "Maroon 5 She Will Be Loved", "type": "track", "price": 14.99, "stock": 20},
    {"query": "Maroon 5 Moves Like Jagger", "type": "track", "price": 14.99, "stock": 20},
    {"query": "Maroon 5 One More Night", "type": "track", "price": 13.99, "stock": 15},
    {"query": "Maroon 5 Memories", "type": "track", "price": 13.99, "stock": 15},
    {"query": "Maroon 5 What Lovers Do SZA", "type": "track", "price": 13.99, "stock": 15},
    {"query": "Maroon 5 Wait", "type": "track", "price": 12.99, "stock": 15},
    {"query": "Maroon 5 Cold Future", "type": "track", "price": 12.99, "stock": 15},
    
    # Anime & J-Pop / Japanese Tracks & Singles
    {"query": "Renai Circulation Kana Hanazawa", "type": "track", "price": 15.99, "stock": 20},
    {"query": "絶頂讃歌 和ぬか", "type": "track", "price": 13.99, "stock": 15},
    {"query": "Rendezvous Kanaria", "type": "track", "price": 13.99, "stock": 15},
    {"query": "HAWATARI NIOKU CENTI MAXIMUM THE HORMONE", "type": "track", "price": 16.99, "stock": 25},
    {"query": "ワンダーランド FLiP", "type": "track", "price": 14.99, "stock": 15},
    {"query": "夜に駆ける YOASOBI", "type": "track", "price": 16.99, "stock": 30},
    {"query": "The Everlasting Guilty Crown EGOIST", "type": "track", "price": 15.99, "stock": 20},
    {"query": "アイウエ MAISONdes", "type": "track", "price": 14.99, "stock": 20},
    {"query": "Masquerade Hitomi Code Geass", "type": "track", "price": 14.99, "stock": 15},
    {"query": "STYX HELIX MYTH & ROID", "type": "track", "price": 15.99, "stock": 20},
    {"query": "可愛くてごめん HoneyWorks", "type": "track", "price": 14.99, "stock": 20},
]


async def run_batch():
    logger.info("Connecting to MongoDB Atlas...")
    await connect_to_mongo()
    
    spotify = SpotifyService()
    sync = SyncService()
    
    for item in BATCH_ITEMS:
        q = item["query"]
        t = item["type"]
        price = item["price"]
        stock = item["stock"]
        
        logger.info(f"Searching Spotify: {q} ({t})")
        try:
            search_res = await spotify.search(q, search_type=t)
            if not search_res:
                logger.warning(f"No results for: {q}")
                continue
                
            if t == "album":
                albums = search_res.get("albums", {}).get("items", [])
                if albums:
                    alb = albums[0]
                    logger.info(f"Syncing Album: '{alb['name']}' by {alb.get('artists', [{}])[0].get('name')}")
                    await sync.sync_album_by_spotify_id(alb["id"], default_price=price, default_stock=stock)
                else:
                    logger.warning(f"No album match found for: {q}")
            else:
                tracks = search_res.get("tracks", {}).get("items", [])
                if tracks:
                    trk = tracks[0]
                    logger.info(f"Syncing Single SKU: '{trk['name']}' by {trk.get('artists', [{}])[0].get('name')}")
                    await sync.sync_track_by_spotify_id(trk["id"], default_price=price, default_stock=stock)
                else:
                    logger.warning(f"No track match found for: {q}")
            
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Error syncing {q}: {e}", exc_info=True)
            
    logger.info("Batch 2 sync finished successfully!")
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(run_batch())
