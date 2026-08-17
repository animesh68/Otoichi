from typing import List
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie

from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

db = MongoDB()

async def get_document_models() -> List:
    """Return all Beanie Document models for initialization."""
    from app.db.models.user import User
    from app.db.models.catalog import Artist, Album, Track
    from app.db.models.product import VinylProduct
    from app.db.models.cart import CartItem
    from app.db.models.order import Order
    from app.db.models.social_and_promo import (
        Wishlist,
        Review,
        Coupon,
        StockNotification,
        StripeWebhookEvent,
    )
    from app.db.models.newsletter import (
        NewsletterSubscriber,
        NewsletterCampaign,
    )
    return [
        User,
        Artist,
        Album,
        Track,
        VinylProduct,
        CartItem,
        Order,
        Wishlist,
        Review,
        Coupon,
        StockNotification,
        StripeWebhookEvent,
        NewsletterSubscriber,
        NewsletterCampaign,
    ]

async def connect_to_mongo(database_url: str = None, db_name: str = None, client: AsyncIOMotorClient = None):
    """Initialize AsyncIOMotorClient and Beanie ODM."""
    url = database_url or settings.DATABASE_URL
    name = db_name or settings.MONGODB_DB_NAME
    
    if client:
        db.client = client
    else:
        logger.info(f"Connecting to MongoDB at {url.split('@')[-1] if '@' in url else url}...")
        db.client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=10000)
    
    db.database = db.client[name]
    models = await get_document_models()
    await init_beanie(database=db.database, document_models=models)
    logger.info(f"Connected to MongoDB database '{name}' and initialized Beanie models.")

async def close_mongo_connection():
    """Close MongoDB connection pool."""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")
