from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = Field(default=None, max_length=100)


class NewsletterSubscribeResponse(BaseModel):
    email: str
    first_name: Optional[str] = None
    status: str
    message: str = "Successfully subscribed to Letters from the Listening Room."


class NewsletterUnsubscribeRequest(BaseModel):
    token: str


class NewsletterUnsubscribeResponse(BaseModel):
    email: str
    status: str = "unsubscribed"
    message: str = "You have been unsubscribed from the weekly newsletter."


class NewsletterCampaignTriggerRequest(BaseModel):
    campaign_date: Optional[str] = None  # e.g. "2026-W34"
    force_retry: bool = False


class NewsletterCampaignResponse(BaseModel):
    id: uuid.UUID
    campaign_date: str
    featured_product_id: uuid.UUID
    subject: str
    status: str
    recipient_count: int = 0
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime


class NewsletterMetricsResponse(BaseModel):
    total_subscribers: int
    active_subscribers: int
    unsubscribed_count: int
    total_campaigns_sent: int
    latest_campaign: Optional[NewsletterCampaignResponse] = None
