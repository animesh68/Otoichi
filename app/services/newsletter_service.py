import logging
import re
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
import uuid

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import generate_unsubscribe_token, verify_unsubscribe_token
from app.db.models.catalog import Album, Artist, Track
from app.db.models.newsletter import NewsletterCampaign, NewsletterSubscriber
from app.db.models.product import VinylProduct
from app.services.resend_service import resend_service
from app.templates.newsletter import (
    render_weekly_newsletter_html,
    render_weekly_newsletter_text,
)

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class NewsletterService:
    """Core domain logic for Otoichi newsletter subscriptions and weekly campaigns."""

    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email address to lowercase stripped string."""
        if not email:
            raise BadRequestException(code="INVALID_EMAIL", message="Email is required")
        cleaned = email.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise BadRequestException(code="INVALID_EMAIL", message="Invalid email address format")
        return cleaned

    @staticmethod
    def get_current_week_identifier() -> str:
        """Return the current Monday date identifier e.g. '2026-W34'."""
        today = date.today()
        # ISO calendar returns (year, week_number, weekday)
        iso_year, iso_week, _ = today.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"

    async def subscribe(self, email: str, first_name: Optional[str] = None) -> NewsletterSubscriber:
        """
        Subscribe or reactivate a user in the newsletter.
        Idempotent: does not duplicate records.
        """
        normalized_email = self.normalize_email(email)
        cleaned_first_name = first_name.strip() if first_name else None

        subscriber = await NewsletterSubscriber.find_one(NewsletterSubscriber.email == normalized_email)

        now = datetime.now(timezone.utc)
        if subscriber:
            if subscriber.status != "subscribed":
                subscriber.status = "subscribed"
                subscriber.subscribed_at = now
                subscriber.unsubscribed_at = None
            if cleaned_first_name:
                subscriber.first_name = cleaned_first_name
            subscriber.updated_at = now
            await subscriber.save()
            logger.info(f"Reactivated newsletter subscription for: {normalized_email}")
        else:
            subscriber = NewsletterSubscriber(
                email=normalized_email,
                first_name=cleaned_first_name,
                status="subscribed",
                subscribed_at=now,
                created_at=now,
                updated_at=now,
            )
            await subscriber.insert()
            logger.info(f"Created new newsletter subscriber: {normalized_email}")

        # Asynchronously sync to Resend contact list
        resend_contact_id = await resend_service.sync_contact(
            email=normalized_email,
            first_name=cleaned_first_name,
            unsubscribed=False,
        )
        if resend_contact_id:
            subscriber.resend_contact_id = resend_contact_id
            await subscriber.save()

        return subscriber

    async def unsubscribe(self, token: str) -> NewsletterSubscriber:
        """
        Unsubscribe a user safely using a signed, tamper-proof token.
        """
        email = verify_unsubscribe_token(token)
        if not email:
            raise BadRequestException(
                code="INVALID_UNSUBSCRIBE_TOKEN",
                message="Invalid or expired unsubscribe link. Please check the URL.",
            )

        subscriber = await NewsletterSubscriber.find_one(NewsletterSubscriber.email == email)
        now = datetime.now(timezone.utc)

        if not subscriber:
            # Create a placeholder record marked as unsubscribed so future broadcasts ignore them
            subscriber = NewsletterSubscriber(
                email=email,
                status="unsubscribed",
                unsubscribed_at=now,
                created_at=now,
                updated_at=now,
            )
            await subscriber.insert()
        else:
            subscriber.status = "unsubscribed"
            subscriber.unsubscribed_at = now
            subscriber.updated_at = now
            await subscriber.save()

        logger.info(f"Unsubscribed user from newsletter: {email}")

        # Update Resend contact state
        await resend_service.sync_contact(email=email, unsubscribed=True)
        return subscriber

    async def select_weekly_featured_product(self) -> VinylProduct:
        """
        Deterministically select an eligible vinyl product for the Monday newsletter.
        Prioritizes:
        1. Products that are in stock (stock_quantity > 0)
        2. Products with complete cover art and metadata
        3. Products not featured in recent campaigns
        """
        # 1. Fetch recent campaign featured product IDs
        recent_campaigns = (
            await NewsletterCampaign.find(NewsletterCampaign.status == "sent")
            .sort("-created_at")
            .limit(20)
            .to_list()
        )
        recently_featured_ids = [c.featured_product_id for c in recent_campaigns]

        # 2. Fetch candidate vinyl products
        candidates = await VinylProduct.find().to_list()
        if not candidates:
            raise NotFoundException(
                code="NO_PRODUCTS_AVAILABLE",
                message="No vinyl products found in the catalog to feature.",
            )

        # 3. Score and filter eligible products
        eligible_scored: List[tuple[int, VinylProduct]] = []
        for prod in candidates:
            # Check album linkage
            album = None
            if prod.album_id:
                album = await Album.find_one(Album.id == prod.album_id)

            has_image = bool(prod.image_urls) or bool(album and album.cover_art_url)
            if not has_image:
                continue

            score = 0
            # Higher score for in-stock
            if prod.stock_quantity > 0:
                score += 10
            # Higher score if not recently featured
            if prod.id not in recently_featured_ids:
                score += 20
            else:
                # If recently featured, place it lower
                recency_index = recently_featured_ids.index(prod.id)
                score += recency_index  # The older the past feature, the higher

            # Bonus for complete description
            if album and album.description:
                score += 5

            eligible_scored.append((score, prod))

        if not eligible_scored:
            # Fallback to the first available product
            return candidates[0]

        # Sort descending by score
        eligible_scored.sort(key=lambda x: x[0], reverse=True)
        return eligible_scored[0][1]

    async def execute_weekly_campaign(
        self, campaign_date: Optional[str] = None, force_retry: bool = False
    ) -> Dict[str, Any]:
        """
        Execute weekly Monday newsletter campaign with database-level idempotency.
        """
        target_week = campaign_date or self.get_current_week_identifier()

        # Check existing campaign for idempotency
        existing = await NewsletterCampaign.find_one(NewsletterCampaign.campaign_date == target_week)
        if existing:
            if existing.status == "sent":
                logger.info(f"Newsletter campaign for {target_week} was already sent (ID: {existing.id}). Skipping.")
                return {
                    "status": "already_sent",
                    "campaign_id": str(existing.id),
                    "campaign_date": target_week,
                    "recipient_count": existing.recipient_count,
                    "message": f"Weekly campaign for {target_week} was already dispatched.",
                }
            elif existing.status == "sending" and not force_retry:
                logger.info(f"Newsletter campaign for {target_week} is already in progress.")
                return {
                    "status": "sending",
                    "campaign_id": str(existing.id),
                    "campaign_date": target_week,
                    "message": "Campaign is currently being processed.",
                }
            campaign = existing
        else:
            featured_product = await self.select_weekly_featured_product()
            now = datetime.now(timezone.utc)
            campaign = NewsletterCampaign(
                campaign_date=target_week,
                featured_product_id=featured_product.id,
                subject="",  # Will be populated below
                status="sending",
                created_at=now,
                updated_at=now,
            )
            await campaign.insert()

        # Fetch product and metadata
        product = await VinylProduct.find_one(VinylProduct.id == campaign.featured_product_id)
        if not product:
            product = await self.select_weekly_featured_product()
            campaign.featured_product_id = product.id

        album = None
        artist_name = "Various Artists"
        album_title = "Selected Vinyl Master"
        cover_art_url = product.image_urls[0] if product.image_urls else None
        description = None
        genre = None
        release_year = None
        audio_preview_url = None

        if product.album_id:
            album = await Album.find_one(Album.id == product.album_id)
            if album:
                album_title = album.title
                artist_name = album.artist_name or "Featured Artist"
                cover_art_url = album.cover_art_url or cover_art_url
                description = album.description
                genre = album.genre
                release_year = album.release_year

                # Find preview URL from tracks
                tracks = await Track.find(Track.album_id == album.id).to_list()
                for trk in tracks:
                    if trk.itunes_preview_url:
                        audio_preview_url = trk.itunes_preview_url
                        break

        if product.track_id and not album:
            track = await Track.find_one(Track.id == product.track_id)
            if track:
                album_title = track.title
                artist_name = track.artist_name or artist_name
                audio_preview_url = track.itunes_preview_url

        subject = f"Letters from the Listening Room: {album_title} by {artist_name}"
        campaign.subject = subject

        # Fetch active subscribers
        subscribers = await NewsletterSubscriber.find(NewsletterSubscriber.status == "subscribed").to_list()
        logger.info(f"Found {len(subscribers)} active subscribers for campaign {target_week}")

        if not subscribers:
            campaign.status = "sent"
            campaign.recipient_count = 0
            campaign.sent_at = datetime.now(timezone.utc)
            campaign.updated_at = datetime.now(timezone.utc)
            await campaign.save()
            return {
                "status": "sent",
                "campaign_id": str(campaign.id),
                "campaign_date": target_week,
                "recipient_count": 0,
                "message": "No active subscribers to send to. Campaign marked complete.",
            }

        # Build personalized email payloads with signed unsubscribe tokens
        email_payloads = []
        for sub in subscribers:
            token = generate_unsubscribe_token(sub.email)
            html = render_weekly_newsletter_html(
                artist_name=artist_name,
                album_title=album_title,
                cover_art_url=cover_art_url,
                description=description,
                format_name=product.format,
                vinyl_variant=product.vinyl_variant,
                price=product.price,
                stock_quantity=product.stock_quantity,
                product_id=str(product.id),
                unsubscribe_token=token,
                audio_preview_url=audio_preview_url,
                genre=genre,
                release_year=release_year,
                subscriber_name=sub.first_name,
            )
            text = render_weekly_newsletter_text(
                artist_name=artist_name,
                album_title=album_title,
                description=description,
                format_name=product.format,
                vinyl_variant=product.vinyl_variant,
                price=product.price,
                product_id=str(product.id),
                unsubscribe_token=token,
                subscriber_name=sub.first_name,
            )
            email_payloads.append({
                "to": sub.email,
                "subject": subject,
                "html": html,
                "text": text,
            })

        # Send via Resend batch API
        try:
            results = await resend_service.send_batch_emails(email_payloads)
            now = datetime.now(timezone.utc)
            campaign.status = "sent"
            campaign.recipient_count = len(subscribers)
            campaign.sent_at = now
            campaign.updated_at = now
            campaign.error_message = None
            if results and isinstance(results, list) and len(results) > 0:
                campaign.resend_broadcast_id = str(results[0].get("id"))
            await campaign.save()
            logger.info(f"Successfully dispatched campaign {target_week} to {len(subscribers)} recipients.")
            return {
                "status": "sent",
                "campaign_id": str(campaign.id),
                "campaign_date": target_week,
                "recipient_count": len(subscribers),
                "featured_product": {
                    "id": str(product.id),
                    "title": album_title,
                    "artist": artist_name,
                    "price": product.price,
                },
            }
        except Exception as e:
            logger.error(f"Failed to dispatch newsletter campaign {target_week}: {e}")
            campaign.status = "failed"
            campaign.error_message = str(e)
            campaign.updated_at = datetime.now(timezone.utc)
            await campaign.save()
            raise


newsletter_service = NewsletterService()
