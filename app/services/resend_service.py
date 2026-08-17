import logging
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResendService:
    """
    Asynchronous client for Resend Email and Contact APIs.
    Gracefully falls back to mock mode if RESEND_API_KEY is not configured.
    """

    BASE_URL = "https://api.resend.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.RESEND_API_KEY
        self.from_email = settings.NEWSLETTER_FROM_EMAIL
        self.from_name = settings.NEWSLETTER_FROM_NAME

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("mock_"))

    @property
    def sender_header(self) -> str:
        if self.from_name:
            return f"{self.from_name} <{self.from_email}>"
        return self.from_email

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def sync_contact(
        self, email: str, first_name: Optional[str] = None, unsubscribed: bool = False
    ) -> Optional[str]:
        """
        Create or update a contact in Resend.
        Does not throw exception if contact creation fails, returns contact_id or None.
        """
        normalized_email = email.strip().lower()
        if not self.is_configured:
            logger.info(f"[Resend Mock] Synced contact {normalized_email} (unsubscribed={unsubscribed})")
            return f"mock_contact_{normalized_email}"

        try:
            payload: Dict[str, Any] = {
                "email": normalized_email,
                "unsubscribed": unsubscribed,
            }
            if first_name:
                payload["first_name"] = first_name.strip()

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.BASE_URL}/contacts",
                    headers=self._get_headers(),
                    json=payload,
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    contact_id = data.get("id") or data.get("data", {}).get("id")
                    logger.info(f"Resend contact synced successfully for {normalized_email} (ID: {contact_id})")
                    return contact_id
                else:
                    logger.warning(
                        f"Resend contact sync returned status {res.status_code} for {normalized_email}: {res.text}"
                    )
                    return None
        except Exception as e:
            logger.warning(f"Failed to sync contact with Resend for {normalized_email}: {e}")
            return None

    async def send_single_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a single email via Resend."""
        normalized_to = to.strip().lower()

        if not self.is_configured:
            logger.info(f"[Resend Mock] Sending email to {normalized_to} with subject: '{subject}'")
            return {"id": f"mock_msg_{normalized_to}", "status": "mock_sent"}

        payload = {
            "from": self.sender_header,
            "to": [normalized_to],
            "subject": subject,
            "html": html,
        }
        if text:
            payload["text"] = text

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.BASE_URL}/emails",
                    headers=self._get_headers(),
                    json=payload,
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    logger.info(f"Resend email sent successfully to {normalized_to} (ID: {data.get('id')})")
                    return data
                else:
                    error_msg = f"Resend email API returned status {res.status_code}: {res.text}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        except Exception as e:
            logger.error(f"Resend email dispatch failed to {normalized_to}: {e}")
            raise

    async def send_batch_emails(self, email_payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Send a batch of emails (up to 100 per Resend API request).
        email_payloads format: [{"to": str, "subject": str, "html": str, "text": str}, ...]
        """
        if not email_payloads:
            return []

        if not self.is_configured:
            logger.info(f"[Resend Mock] Batch sending {len(email_payloads)} emails.")
            return [{"id": f"mock_batch_{i}", "status": "mock_sent"} for i in range(len(email_payloads))]

        results = []
        # Chunk into slices of 100 (Resend limit per batch endpoint)
        chunk_size = 100
        for i in range(0, len(email_payloads), chunk_size):
            chunk = email_payloads[i : i + chunk_size]
            formatted_chunk = []
            for item in chunk:
                to_addr = item["to"].strip().lower()
                msg = {
                    "from": self.sender_header,
                    "to": [to_addr],
                    "subject": item["subject"],
                    "html": item["html"],
                }
                if item.get("text"):
                    msg["text"] = item["text"]
                formatted_chunk.append(msg)

            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{self.BASE_URL}/emails/batch",
                    headers=self._get_headers(),
                    json=formatted_chunk,
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    batch_data = data.get("data", []) if isinstance(data, dict) else data
                    results.extend(batch_data)
                    logger.info(f"Dispatched batch of {len(chunk)} emails via Resend.")
                else:
                    error_msg = f"Resend batch email dispatch returned status {res.status_code}: {res.text}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

        return results


resend_service = ResendService()
