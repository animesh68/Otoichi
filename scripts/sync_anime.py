import asyncio
import logging
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.services.sync_service import SyncService
from app.services.spotify_service import SpotifyService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_anime")

ANIME_JPOP_ITEMS = [
    {"query": "恋愛サーキュレーション 花澤香菜", "price": 15.99, "stock": 20},
    {"query": "絶頂讃歌 和ぬか", "price": 13.99, "stock": 15},
    {"query": "Rendezvous Kanaria", "price": 13.99, "stock": 15},
    {"query": "刃渡り2億センチ MAXIMUM THE HORMONE", "price": 16.99, "stock": 25},
    {"query": "ワンダーランド FLiP", "price": 14.99, "stock": 15},
    {"query": "夜に駆ける YOASOBI", "price": 16.99, "stock": 30},
    {"query": "The Everlasting Guilty Crown EGOIST", "price": 15.99, "stock": 20},
    {"query": "アイウエ MAISONdes", "price": 14.99, "stock": 20},
    {"query": "Masquerade Hitomi Code Geass", "price": 14.99, "stock": 15},
    {"query": "STYX HELIX MYTH & ROID", "price": 15.99, "stock": 20},
    {"query": "可愛くてごめん HoneyWorks", "price": 14.99, "stock": 20},
]


async def run_anime_sync():
    await connect_to_mongo()
    spotify = SpotifyService()
    sync = SyncService()
    
    for it in ANIME_JPOP_ITEMS:
        q = it["query"]
        p = it["price"]
        s = it["stock"]
        
        logger.info(f"Syncing Anime/J-Pop single: {q}")
        search_res = await spotify.search(q, search_type="track")
        if not search_res:
            continue
        tracks = search_res.get("tracks", {}).get("items", [])
        if tracks:
            trk = tracks[0]
            logger.info(f"Adding single product SKU for '{trk['name']}' ({trk['id']})")
            await sync.sync_track_by_spotify_id(trk["id"], default_price=p, default_stock=s)
            
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_anime_sync())
