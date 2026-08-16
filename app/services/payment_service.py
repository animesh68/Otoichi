from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional
import stripe

from app.core.config import settings
from app.core.exceptions import BadRequestException, PaymentFailedException

logger = logging.getLogger(__name__)


class BasePaymentService(ABC):
    @abstractmethod
    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a payment intent / charge request with the payment provider."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature_header: str,
    ) -> Dict[str, Any]:
        """Verify the authenticity of incoming webhook payload."""
        pass


class StripePaymentService(BasePaymentService):
    def __init__(self):
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.currency = settings.STRIPE_CURRENCY or "usd"
        if self.secret_key:
            stripe.api_key = self.secret_key

    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent with server-authoritative amount and idempotency protection.
        Amount is converted to lowest denomination (cents for USD).
        """
        amount_cents = int(round(amount * 100))
        if amount_cents <= 0:
            raise BadRequestException(message="Payment amount must be greater than zero")

        # In production, require valid Stripe credentials
        if settings.ENVIRONMENT == "production" and not self.secret_key:
            logger.critical("STRIPE_SECRET_KEY is not configured in production environment.")
            raise PaymentFailedException(message="Payment gateway configuration error")

        if not self.secret_key:
            if not settings.ALLOW_MOCK_PAYMENTS:
                raise PaymentFailedException(message="Stripe credentials are missing and mock mode is disabled")
            
            # Explicit local development / test mock intent
            mock_id = f"pi_mock_{amount_cents}_{idempotency_key or 'dev'}"
            logger.info("Using development mock Stripe PaymentIntent (no STRIPE_SECRET_KEY configured).")
            return {
                "id": mock_id,
                "client_secret": f"{mock_id}_secret_mock",
                "amount": amount_cents,
                "currency": currency.lower(),
                "status": "requires_payment_method",
            }

        try:
            # Clean and sanitize metadata - never include sensitive information
            safe_metadata = {}
            if metadata:
                for k, v in metadata.items():
                    if v is not None:
                        safe_metadata[str(k)] = str(v)[:500]

            kwargs: Dict[str, Any] = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "metadata": safe_metadata,
                "automatic_payment_methods": {"enabled": True},
            }
            if idempotency_key:
                kwargs["idempotency_key"] = idempotency_key

            intent = stripe.PaymentIntent.create(**kwargs)
            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
            }
        except stripe.StripeError as e:
            logger.error(f"Stripe PaymentIntent creation failed: {e.__class__.__name__}")
            raise PaymentFailedException(message=f"Stripe error: {getattr(e, 'user_message', str(e))}")
        except Exception as e:
            logger.error(f"Unexpected error in Stripe payment service: {e}")
            raise PaymentFailedException(message="Could not initialize payment")

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature_header: str,
    ) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature header using raw payload bytes.
        """
        if not self.webhook_secret:
            if settings.ENVIRONMENT == "production":
                logger.critical("STRIPE_WEBHOOK_SECRET is not configured in production.")
                raise BadRequestException(code="WEBHOOK_CONFIG_ERROR", message="Webhook secret not configured")
            
            # Dev / test mode fallback
            import json
            try:
                return json.loads(payload.decode("utf-8"))
            except Exception:
                raise BadRequestException(code="INVALID_WEBHOOK_PAYLOAD", message="Malformed webhook JSON")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature_header,
                secret=self.webhook_secret,
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Invalid Stripe webhook signature: {e}")
            raise BadRequestException(code="INVALID_WEBHOOK_SIGNATURE", message="Stripe signature verification failed")
        except Exception as e:
            logger.error(f"Error parsing Stripe webhook: {e}")
            raise BadRequestException(code="INVALID_WEBHOOK_PAYLOAD", message="Malformed webhook event")


# Global payment service instance
payment_service: BasePaymentService = StripePaymentService()
