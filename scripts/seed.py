import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import uuid

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.catalog import Album, Artist, Track
from app.db.models.order import Order, OrderItem
from app.db.models.product import VinylProduct
from app.db.models.social_and_promo import Coupon
from app.db.models.user import Address, User
from app.db.mongo import connect_to_mongo, close_mongo_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


async def seed_users():
    """Seed initial admin and customer users if not already existing."""
    users_data = [
        {
            "email": "admin@otoichi.com",
            "password": "AdminPassword123!",
            "full_name": "Otoichi Administrator",
            "role": "admin",
        },
        {
            "email": "customer@otoichi.com",
            "password": "CustomerPassword123!",
            "full_name": "Miles Davis Fan",
            "role": "customer",
        },
    ]

    for u_data in users_data:
        email_clean = u_data["email"].lower().strip()
        user = await User.find_one(User.email == email_clean)
        if not user:
            user = User(
                email=email_clean,
                password_hash=get_password_hash(u_data["password"]),
                full_name=u_data["full_name"],
                role=u_data["role"],
                is_active=True,
            )

            # Seed default address for customer
            if user.role == "customer":
                addr = Address(
                    id=uuid.uuid4(),
                    line1="123 Vinyl Groove Way",
                    line2="Apt 4B",
                    city="Tokyo",
                    state="Shibuya",
                    postal_code="150-0042",
                    country="Japan",
                    phone="+81 3-1234-5678",
                    is_default=True,
                )
                user.addresses.append(addr)

            await user.insert()
            logger.info(f"Seeded user: {user.email} ({user.role})")


async def seed_coupons():
    """Seed sample promotional coupons."""
    coupons = [
        {"code": "VINYL10", "discount_type": "percent", "value": 10.0, "usage_limit": 100},
        {"code": "SAVE5", "discount_type": "fixed", "value": 5.0, "usage_limit": 50},
        {"code": "VIP20", "discount_type": "percent", "value": 20.0, "usage_limit": 20},
    ]

    for c in coupons:
        code_clean = c["code"].strip().upper()
        existing = await Coupon.find_one(Coupon.code == code_clean)
        if not existing:
            coupon = Coupon(
                code=code_clean,
                discount_type=c["discount_type"],
                value=c["value"],
                usage_limit=c["usage_limit"],
                is_active=True,
            )
            await coupon.insert()
            logger.info(f"Seeded coupon: {c['code']}")


async def seed_catalog_from_json(json_path: Path):
    """Read seed_data.json and create Artists, Albums, Tracks, and VinylProducts idempotently."""
    if not json_path.exists():
        logger.error(f"Seed data file not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        artist_name = item["artist_name"]
        spotify_artist_id = item.get("spotify_artist_id")

        # 1. Artist
        artist = await Artist.find_one(Artist.name == artist_name)
        if not artist:
            artist = Artist(name=artist_name, spotify_artist_id=spotify_artist_id)
            await artist.insert()
            logger.info(f"Created artist: {artist.name}")
        elif spotify_artist_id and not artist.spotify_artist_id:
            artist.spotify_artist_id = spotify_artist_id
            await artist.save()

        # 2. Album vs Standalone Single
        if item.get("type") == "album":
            album = await Album.find_one(Album.title == item["title"], Album.artist_id == artist.id)
            if not album:
                album = Album(
                    title=item["title"],
                    artist_id=artist.id,
                    artist_name=artist.name,
                    release_year=item.get("release_year"),
                    genre=item.get("genre", "Rock"),
                    description=item.get("description"),
                    cover_art_url=item.get("cover_art_url"),
                    spotify_album_id=item.get("spotify_album_id"),
                    label=item.get("label"),
                )
                await album.insert()
                logger.info(f"Created album: {album.title}")

            for t_data in item.get("tracks", []):
                track = await Track.find_one(Track.album_id == album.id, Track.title == t_data["title"])
                if not track:
                    track = Track(
                        album_id=album.id,
                        artist_id=artist.id,
                        title=t_data["title"],
                        track_number=t_data.get("track_number"),
                        duration_ms=t_data.get("duration_ms"),
                        spotify_track_id=t_data.get("spotify_track_id"),
                        itunes_preview_url=t_data.get("itunes_preview_url"),
                        is_standalone_single=False,
                    )
                    await track.insert()

            product = await VinylProduct.find_one(VinylProduct.sku == item["sku"])
            if not product:
                product = VinylProduct(
                    product_type="album",
                    album_id=album.id,
                    format=item.get("format", "LP"),
                    vinyl_variant=item.get("vinyl_variant", "standard"),
                    price=float(item["price"]),
                    currency="USD",
                    stock_quantity=int(item.get("stock_quantity", 25)),
                    sku=item["sku"],
                    is_preorder=item.get("is_preorder", False),
                    image_urls=[item["cover_art_url"]] if item.get("cover_art_url") else [],
                )
                await product.insert()
                logger.info(f"Created vinyl product SKU: {product.sku}")

        elif item.get("type") == "single":
            track_info = item.get("track", {})
            track = await Track.find_one(Track.album_id == None, Track.title == track_info.get("title", item["title"]))
            if not track:
                track = Track(
                    album_id=None,
                    artist_id=artist.id,
                    title=track_info.get("title", item["title"]),
                    duration_ms=track_info.get("duration_ms"),
                    spotify_track_id=track_info.get("spotify_track_id"),
                    itunes_preview_url=track_info.get("itunes_preview_url"),
                    is_standalone_single=True,
                )
                await track.insert()
                logger.info(f"Created standalone single track: {track.title}")

            product = await VinylProduct.find_one(VinylProduct.sku == item["sku"])
            if not product:
                product = VinylProduct(
                    product_type="single",
                    track_id=track.id,
                    format=item.get("format", "7\""),
                    vinyl_variant=item.get("vinyl_variant", "standard"),
                    price=float(item["price"]),
                    currency="USD",
                    stock_quantity=int(item.get("stock_quantity", 15)),
                    sku=item["sku"],
                    is_preorder=item.get("is_preorder", False),
                    image_urls=[item["cover_art_url"]] if item.get("cover_art_url") else [],
                )
                await product.insert()
                logger.info(f"Created vinyl single product SKU: {product.sku}")


async def seed_delivered_order_for_review():
    """Seed a sample delivered order so review eligibility can be tested immediately."""
    customer = await User.find_one(User.email == "customer@otoichi.com")
    if not customer:
        return

    # Check if a delivered order already exists
    existing_order = await Order.find_one(Order.user_id == customer.id, Order.status == "delivered")
    if existing_order:
        return

    # Find a product to put in the delivered order
    product = await VinylProduct.find_one(VinylProduct.product_type == "album")
    if not product:
        return

    album = await Album.find_one(Album.id == product.album_id) if product.album_id else None
    title = f"{album.title} ({product.format}, {product.vinyl_variant})" if album else "Vinyl Album"

    order = Order(
        user_id=customer.id,
        status="delivered",
        subtotal_amount=float(product.price),
        shipping_amount=5.00,
        discount_amount=0.0,
        total_amount=float(product.price) + 5.00,
        currency="USD",
        shipping_address_snapshot={
            "line1": "123 Vinyl Groove Way",
            "city": "Tokyo",
            "postal_code": "150-0042",
            "country": "Japan",
        },
        items=[
            OrderItem(
                id=uuid.uuid4(),
                product_id=product.id,
                quantity=1,
                unit_price_at_purchase=float(product.price),
                product_title_snapshot=title,
            )
        ],
    )
    await order.insert()
    logger.info(f"Seeded delivered order for review testing for customer: {customer.email}")


async def run_seed():
    """Main seeder runner."""
    logger.info("Connecting to MongoDB for seeding...")
    await connect_to_mongo()

    try:
        json_path = Path(__file__).parent.parent / "data" / "seed_data.json"
        logger.info(f"Loading seed data from {json_path}...")

        await seed_users()
        await seed_coupons()
        await seed_catalog_from_json(json_path)
        await seed_delivered_order_for_review()

        logger.info("Database seeding completed successfully!")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(run_seed())
