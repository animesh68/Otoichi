import asyncio
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct

async def main():
    await connect_to_mongo()
    
    print("=== INSPECTING ALBUMS MATCHING 'Tongues' OR 'hormone' ===")
    albums = await Album.find().to_list()
    for a in albums:
        if 'tongues' in a.title.lower() or 'hormone' in a.title.lower() or 'maximum' in a.title.lower():
            tracks = await Track.find(Track.album_id == a.id).to_list()
            prods = await VinylProduct.find(VinylProduct.album_id == a.id).to_list()
            print(f"Album ID: {a.id} | Title: {a.title} | Artist: {a.artist_name} | Spotify ID: {a.spotify_album_id}")
            print(f"  Tracks ({len(tracks)}): {[t.title for t in tracks]}")
            print(f"  Products: {[p.id for p in prods]}")

    print("\n=== INSPECTING PRODUCTS MATCHING 'Tongues' OR 'hormone' ===")
    prods = await VinylProduct.find().to_list()
    for p in prods:
        alb = await Album.find_one(Album.id == p.album_id) if p.album_id else None
        trk = await Track.find_one(Track.id == p.track_id) if p.track_id else None
        title = alb.title if alb else (trk.title if trk else "None")
        if 'tongues' in title.lower() or 'hormone' in title.lower() or 'maximum' in title.lower():
            print(f"Prod ID: {p.id} | Type: {p.product_type} | SKU: {p.sku} | Alb ID: {p.album_id} | Trk ID: {p.track_id} | Title: {title}")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
