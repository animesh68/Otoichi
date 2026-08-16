from datetime import datetime, timezone
from typing import Optional
import uuid
import pymongo
from pydantic import Field
from beanie import Document


class CartItem(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: Optional[uuid.UUID] = Field(default=None, index=True)
    session_id: Optional[str] = Field(default=None, index=True)
    product_id: uuid.UUID = Field(index=True)
    quantity: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "cart_items"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("product_id", pymongo.ASCENDING)],
                unique=True,
                partialFilterExpression={"user_id": {"$type": "binData"}},
            ),
            pymongo.IndexModel(
                [("session_id", pymongo.ASCENDING), ("product_id", pymongo.ASCENDING)],
                unique=True,
                partialFilterExpression={"session_id": {"$type": "string"}},
            ),
        ]
