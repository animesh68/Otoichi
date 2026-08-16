import asyncio
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct


async def summary():
    await connect_to_mongo()
    artists = await Artist.find().to_list()
    albums = await Album.find().to_list()
    tracks = await Track.find().to_list()
    products = await VinylProduct.find().to_list()

    print("================ LIVE MONGO DB CATALOG SUMMARY ================")
    print(f"Total Artists: {len(artists)}")
    print(f"Total Albums: {len(albums)}")
    print(f"Total Tracks: {len(tracks)}")
    print(f"Total Sellable Vinyl SKUs: {len(products)}")

    print("\n--- ALL ALBUMS IN DATABASE ---")
    for a in albums:
        print(f"* \"{a.title}\" by {a.artist_name} ({a.release_year}, {a.genre}) | Cover Art: {'YES' if a.cover_art_url else 'NO'}")

    singles = [p for p in products if p.product_type == "single"]
    print(f"\n--- ALL STANDALONE VINYL SINGLES IN DATABASE ({len(singles)}) ---")
    for p in singles:
        t = await Track.find_one(Track.id == p.track_id)
        artist = await Artist.find_one(Artist.id == t.artist_id) if t else None
        art_name = artist.name if artist else "Unknown"
        t_name = t.title if t else "Unknown"
        prev = "YES" if t and t.itunes_preview_url else "NO"
        line = f"* Single SKU: {p.sku} | \"{t_name}\" by {art_name} | Format: {p.format} | Price: ${p.price} | Stock: {p.stock_quantity} | Audio Preview: {prev}"
        print(line.encode("ascii", "replace").decode("ascii"))

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(summary())
