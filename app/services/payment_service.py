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
        if self.secret_key:
            stripe.api_key = self.secret_key

    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent.
        Amount is converted to lowest denomination (cents for USD).
        """
        amount_cents = int(round(amount * 100))
        if amount_cents < 50:
            # Minimum allowed by Stripe
            amount_cents = 50

        if not self.secret_key:
            # Mock payment intent for dev/testing when Stripe key is not set
            mock_id = f"pi_mock_{amount_cents}_{metadata.get('user_id', 'anon') if metadata else 'anon'}"
            return {
                "id": mock_id,
                "client_secret": f"{mock_id}_secret_mock",
                "amount": amount_cents,
                "currency": currency.lower(),
                "status": "requires_payment_method",
            }

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )
            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
            }
        except stripe.StripeError as e:
            logger.error(f"Stripe PaymentIntent creation failed: {e}")
            raise PaymentFailedException(message=f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in payment service: {e}")
            raise PaymentFailedException(message="Could not initialize payment")

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature_header: str,
    ) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature header.
        Raises BadRequestException if invalid.
        """
        if not self.webhook_secret:
            # In local test/mock mode if webhook secret is not set, parse payload directly
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
