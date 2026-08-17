from datetime import datetime, timezone
from typing import Optional
import uuid
from pydantic import Field
from beanie import Document, Indexed
import pymongo


class NewsletterSubscriber(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: Indexed(str, unique=True)
    first_name: Optional[str] = None
    status: str = "subscribed"  # "subscribed", "unsubscribed"
    resend_contact_id: Optional[str] = None
    subscribed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    unsubscribed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "newsletter_subscribers"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("status", pymongo.ASCENDING)]),
        ]


class NewsletterCampaign(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    campaign_date: Indexed(str, unique=True)  # Format: "YYYY-Www" or "YYYY-MM-DD" e.g. "2026-W34"
    featured_product_id: uuid.UUID = Field(index=True)
    subject: str
    status: str = "scheduled"  # "scheduled", "sending", "sent", "failed"
    recipient_count: int = 0
    resend_broadcast_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "newsletter_campaigns"
        indexes = [
            pymongo.IndexModel([("campaign_date", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("status", pymongo.ASCENDING)]),
            pymongo.IndexModel([("featured_product_id", pymongo.ASCENDING)]),
        ]
