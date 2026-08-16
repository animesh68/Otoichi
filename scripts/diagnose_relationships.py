import asyncio
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct

async def main():
    await connect_to_mongo()
    print("=== CHECKING ALL ALBUMS IN DB ===")
    albums = await Album.find().to_list()
    for a in albums:
        artist = await Artist.find_one(Artist.id == a.artist_id) if a.artist_id else None
        tracks = await Track.find(Track.album_id == a.id).sort(+Track.track_number).to_list()
        prods = await VinylProduct.find(VinylProduct.album_id == a.id).to_list()
        print(f"\n[Album ID: {a.id}]")
        print(f"  Title: '{a.title}'")
        print(f"  Artist Name in Album: '{a.artist_name}' | Artist Doc: '{artist.name if artist else None}'")
        print(f"  Spotify ID: {a.spotify_album_id}")
        print(f"  Linked Vinyl Products: {[p.sku for p in prods]}")
        print(f"  Tracks ({len(tracks)}): {[t.title for t in tracks[:4]]}...")

    print("\n=== CHECKING ALL VINYL PRODUCTS ===")
    products = await VinylProduct.find().to_list()
    for p in products:
        alb = await Album.find_one(Album.id == p.album_id) if p.album_id else None
        trk = await Track.find_one(Track.id == p.track_id) if p.track_id else None
        print(f"Product ID: {p.id} | Type: {p.product_type} | SKU: {p.sku} | Album: '{alb.title if alb else None}' | Track: '{trk.title if trk else None}'")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
