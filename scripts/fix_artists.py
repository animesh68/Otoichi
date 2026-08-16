import asyncio
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct
from app.services.spotify_service import SpotifyService

async def fix():
    await connect_to_mongo()
    spotify = SpotifyService()
    
    albums = await Album.find().to_list()
    print(f"Total Albums in DB: {len(albums)}")
    
    for a in albums:
        artist = await Artist.find_one(Artist.id == a.artist_id) if a.artist_id else None
        artist_name = artist.name if (artist and artist.name and artist.name != "Unknown Artist") else a.artist_name
        
        # If artist_name is missing or Unknown, look it up on Spotify via spotify_album_id
        if (not artist_name or artist_name == "Unknown Artist" or artist_name == "Various Artists") and a.spotify_album_id:
            print(f"Looking up Spotify data for album: '{a.title}' ({a.spotify_album_id})...")
            alb_data = await spotify.get_album(a.spotify_album_id)
            if alb_data:
                artists = alb_data.get("artists", [])
                if artists:
                    real_name = artists[0].get("name")
                    real_spotify_id = artists[0].get("id")
                    print(f" -> Found real artist: '{real_name}'")
                    
                    art_doc = await Artist.find_one(Artist.name == real_name)
                    if not art_doc:
                        art_doc = Artist(name=real_name, spotify_artist_id=real_spotify_id)
                        await art_doc.insert()
                    
                    a.artist_id = art_doc.id
                    a.artist_name = real_name
                    await a.save()
                    artist_name = real_name
        elif artist and not a.artist_name:
            a.artist_name = artist.name
            await a.save()
            
        print(f"Album: '{a.title}' -> Artist: '{a.artist_name}' (ID: {a.artist_id})")

    # Also check tracks and their artists
    tracks = await Track.find().to_list()
    print(f"\nTotal Tracks in DB: {len(tracks)}")
    for t in tracks:
        if t.album_id:
            alb = await Album.find_one(Album.id == t.album_id)
            if alb and (not t.artist_id or not getattr(t, 'artist_name', None)):
                t.artist_id = alb.artist_id
                t.artist_name = alb.artist_name
                await t.save()
        elif t.artist_id:
            art = await Artist.find_one(Artist.id == t.artist_id)
            if art:
                t.artist_name = art.name
                await t.save()

    await close_mongo_connection()
    print("Artist update complete!")

if __name__ == "__main__":
    asyncio.run(fix())
