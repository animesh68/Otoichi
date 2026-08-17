import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request, status, Depends

from app.core.config import settings
from app.core.dependencies import get_optional_current_user
from app.db.models.user import User
from app.schemas.newsletter import (
    NewsletterCampaignTriggerRequest,
    NewsletterSubscribeRequest,
    NewsletterSubscribeResponse,
    NewsletterUnsubscribeRequest,
    NewsletterUnsubscribeResponse,
)
from app.services.newsletter_service import newsletter_service

logger = logging.getLogger(__name__)

newsletter_router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


def verify_cron_or_admin(
    authorization: Optional[str] = Header(default=None),
    x_cron_secret: Optional[str] = Header(default=None),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> bool:
    """
    Verify scheduler authorization using CRON_SECRET or Admin user credentials.
    Supports:
    - Header: Authorization: Bearer <CRON_SECRET>
    - Header: X-Cron-Secret: <CRON_SECRET>
    - Authenticated Admin user session
    """
    cron_secret = settings.CRON_SECRET

    # Check X-Cron-Secret header
    if x_cron_secret and cron_secret and x_cron_secret.strip() == cron_secret.strip():
        return True

    # Check Bearer cron token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
        if cron_secret and token == cron_secret.strip():
            return True

    # Check Admin role
    if current_user and current_user.role == "admin":
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid CRON_SECRET or Admin authorization required to trigger newsletter.",
    )


@newsletter_router.post("/subscribe", response_model=NewsletterSubscribeResponse)
async def subscribe_to_newsletter(req: NewsletterSubscribeRequest):
    """
    Subscribe an email address to 'Letters from the Listening Room'.
    Idempotent and safe against duplicates.
    """
    subscriber = await newsletter_service.subscribe(
        email=req.email,
        first_name=req.first_name,
    )
    return NewsletterSubscribeResponse(
        email=subscriber.email,
        first_name=subscriber.first_name,
        status=subscriber.status,
        message="You have successfully subscribed to Letters from the Listening Room.",
    )


@newsletter_router.post("/unsubscribe", response_model=NewsletterUnsubscribeResponse)
async def unsubscribe_from_newsletter(req: NewsletterUnsubscribeRequest):
    """
    Unsubscribe a user from the newsletter using a secure signed token.
    """
    subscriber = await newsletter_service.unsubscribe(token=req.token)
    return NewsletterUnsubscribeResponse(
        email=subscriber.email,
        status=subscriber.status,
        message="You have been successfully unsubscribed from the weekly newsletter.",
    )


@newsletter_router.post("/trigger-weekly")
async def trigger_weekly_newsletter(
    req: NewsletterCampaignTriggerRequest = NewsletterCampaignTriggerRequest(),
    authorized: bool = Depends(verify_cron_or_admin),
):
    """
    Protected server-side endpoint for the Monday newsletter job.
    Enforces strict idempotency per ISO week to prevent duplicate sends.
    """
    result = await newsletter_service.execute_weekly_campaign(
        campaign_date=req.campaign_date,
        force_retry=req.force_retry,
    )
    return result
