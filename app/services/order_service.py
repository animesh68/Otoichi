from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.core.config import settings
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException, InsufficientStockException
from app.db.models.cart import CartItem
from app.db.models.catalog import Album, Track
from app.db.models.order import Order, OrderItem
from app.db.models.product import VinylProduct
from app.db.models.user import User
from app.services.coupon_service import CouponService
from app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)


class OrderService:
    VALID_STATUS_TRANSITIONS = {
        "pending": ["paid", "processing", "cancelled"],
        "paid": ["processing", "shipped", "cancelled", "refunded"],
        "processing": ["shipped", "cancelled", "refunded"],
        "shipped": ["delivered", "cancelled", "refunded"],
        "delivered": ["refunded"],
        "cancelled": [],
        "refunded": [],
    }

    def __init__(self, db=None):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.coupon_service = CouponService(db)

    async def calculate_checkout_summary(
        self,
        user_id: uuid.UUID,
        coupon_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Authoritative server-side price, coupon discount, shipping, and total calculation.
        """
        cart_items = await CartItem.find(CartItem.user_id == user_id).to_list()
        if not cart_items:
            raise BadRequestException(message="Cannot calculate checkout for an empty cart")

        subtotal = 0.0
        item_count = 0

        for item in cart_items:
            product = await VinylProduct.find_one(VinylProduct.id == item.product_id)
            if not product:
                raise NotFoundException(message=f"Product {item.product_id} no longer exists")
            if product.stock_quantity < item.quantity:
                raise InsufficientStockException(
                    message=f"Insufficient stock for {product.sku}. Only {product.stock_quantity} available."
                )
            subtotal += float(product.price) * item.quantity
            item_count += item.quantity

        subtotal = round(subtotal, 2)
        discount_amount = 0.0
        coupon_obj = None

        if coupon_code:
            coupon_obj, discount_amount = await self.coupon_service.get_and_validate_coupon(
                code=coupon_code,
                subtotal=subtotal,
                for_update=False,
            )
            discount_amount = round(discount_amount, 2)

        # Unified free shipping rule: Free if subtotal >= threshold, else flat rate
        shipping_amount = 0.0 if subtotal >= settings.FREE_SHIPPING_THRESHOLD else float(settings.FLAT_SHIPPING_RATE)

        # If 100% coupon applied, waive shipping as well so total is $0.00
        if coupon_obj and getattr(coupon_obj, "discount_type", None) == "percent" and float(getattr(coupon_obj, "value", 0)) >= 100.0:
            shipping_amount = 0.0

        total_amount = max(0.0, round(subtotal + shipping_amount - discount_amount, 2))
        is_zero_total = total_amount <= 0.0

        return {
            "subtotal": subtotal,
            "shipping": shipping_amount,
            "discount": discount_amount,
            "total": total_amount,
            "currency": settings.DEFAULT_CURRENCY,
            "item_count": item_count,
            "coupon": coupon_obj,
            "is_zero_total": is_zero_total,
        }

    async def prepare_order_and_items(
        self,
        user: User,
        shipping_address_id: Optional[uuid.UUID] = None,
        shipping_address_data: Optional[Dict[str, Any]] = None,
        coupon_code: Optional[str] = None,
        checkout_id: Optional[str] = None,
    ) -> Tuple[Order, List[Tuple[VinylProduct, int]]]:
        """
        Constructs Order and OrderItem records from cart and snapshot metadata.
        """
        summary = await self.calculate_checkout_summary(user.id, coupon_code)
        cart_items = await CartItem.find(CartItem.user_id == user.id).to_list()

        address_snapshot = None
        if shipping_address_id:
            addr = next((a for a in user.addresses if a.id == shipping_address_id), None)
            if not addr:
                raise NotFoundException(code="ADDRESS_NOT_FOUND", message="Shipping address not found")
            address_snapshot = {
                "line1": addr.line1,
                "line2": addr.line2,
                "city": addr.city,
                "state": addr.state,
                "postal_code": addr.postal_code,
                "country": addr.country,
                "phone": addr.phone,
            }
        elif shipping_address_data:
            address_snapshot = shipping_address_data

        order_items: List[OrderItem] = []
        product_quantities: List[Tuple[VinylProduct, int]] = []

        for item in cart_items:
            product = await VinylProduct.find_one(VinylProduct.id == item.product_id)
            if not product:
                raise NotFoundException(message="Product in cart not found")

            title = "Vinyl Item"
            if product.album_id:
                album = await Album.find_one(Album.id == product.album_id)
                if album:
                    title = f"{album.title} ({product.format})"
            elif product.track_id:
                track = await Track.find_one(Track.id == product.track_id)
                if track:
                    title = f"{track.title} ({product.format})"

            item_price = float(product.price)
            order_items.append(
                OrderItem(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price_at_purchase=item_price,
                    product_title_snapshot=title,
                )
            )
            product_quantities.append((product, item.quantity))

        coupon_obj = summary.get("coupon")
        order = Order(
            user_id=user.id,
            status="pending",
            payment_status="requires_payment_method",
            subtotal_amount=summary["subtotal"],
            shipping_amount=summary["shipping"],
            discount_amount=summary["discount"],
            total_amount=summary["total"],
            currency=settings.DEFAULT_CURRENCY,
            shipping_address_snapshot=address_snapshot,
            coupon_id=coupon_obj.id if coupon_obj else None,
            coupon_code_snapshot=coupon_obj.code if coupon_obj else None,
            checkout_id=checkout_id or f"chk_{uuid.uuid4().hex[:12]}",
            items=order_items,
        )
        return order, product_quantities

    async def fulfill_paid_order(
        self,
        payment_intent_id: str,
        payment_method_type: Optional[str] = "card",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Order]:
        """
        Idempotent order fulfillment upon Stripe payment_intent.succeeded webhook.
        Safely commits inventory decrements, marks payment succeeded, and clears cart.
        """
        order = await Order.find_one(Order.stripe_payment_intent_id == payment_intent_id)
        if not order and metadata:
            checkout_id = metadata.get("checkout_id")
            if checkout_id:
                order = await Order.find_one(Order.checkout_id == checkout_id)

        if not order:
            logger.warning(f"No existing Order found for PaymentIntent {payment_intent_id}")
            return None

        # Idempotency: if already marked paid, return safely
        if order.payment_status == "succeeded" and order.status in ["paid", "processing", "shipped", "delivered"]:
            logger.info(f"Order {order.id} is already fulfilled. Skipping duplicate.")
            return order

        # Decrement inventory safely for each item
        for item in order.items:
            try:
                await self.inventory_service.lock_and_decrement_stock(item.product_id, item.quantity)
            except Exception as e:
                logger.error(f"Error decrementing inventory for product {item.product_id} on order {order.id}: {e}")

        # Increment coupon usage safely
        if order.coupon_id:
            try:
                await self.coupon_service.increment_coupon_usage(order.coupon_id)
            except Exception as e:
                logger.error(f"Error incrementing coupon {order.coupon_id} usage on order {order.id}: {e}")

        # Mark Order as Paid and Succeeded
        now = datetime.now(timezone.utc)
        order.payment_status = "succeeded"
        order.status = "paid"
        order.paid_at = now
        order.payment_method_type = payment_method_type
        order.updated_at = now
        await order.save()

        # Clear cart for user
        await CartItem.find(CartItem.user_id == order.user_id).delete()
        logger.info(f"Order {order.id} successfully fulfilled and paid via PaymentIntent {payment_intent_id}")
        return order

    async def create_zero_total_order(
        self,
        user: User,
        shipping_address_id: Optional[uuid.UUID] = None,
        shipping_address_data: Optional[Dict[str, Any]] = None,
        coupon_code: Optional[str] = None,
    ) -> Order:
        """
        Direct fulfillment for 100% coupon discounted zero-total orders without creating a Stripe intent.
        """
        summary = await self.calculate_checkout_summary(user.id, coupon_code)
        if summary["total"] > 0.0:
            raise BadRequestException(message="This order has a non-zero total and requires payment")

        order, product_quantities = await self.prepare_order_and_items(
            user=user,
            shipping_address_id=shipping_address_id,
            shipping_address_data=shipping_address_data,
            coupon_code=coupon_code,
        )

        # Commit stock and coupon usage
        for product, qty in product_quantities:
            await self.inventory_service.lock_and_decrement_stock(product.id, qty)

        if order.coupon_id:
            await self.coupon_service.increment_coupon_usage(order.coupon_id)

        now = datetime.now(timezone.utc)
        order.status = "paid"
        order.payment_status = "succeeded"
        order.paid_at = now
        order.payment_method_type = "coupon_free"
        await order.insert()

        # Clear cart
        await CartItem.find(CartItem.user_id == user.id).delete()
        return order

    async def get_order_by_id(self, order_id: uuid.UUID, user: Optional[User] = None) -> Order:
        """Fetch order details. Enforces user ownership unless admin."""
        order = await Order.find_one(Order.id == order_id)
        if not order:
            raise NotFoundException(code="ORDER_NOT_FOUND", message="Order not found")

        if user and user.role != "admin" and order.user_id != user.id:
            raise ForbiddenException(message="You do not have permission to view this order")

        return order

    async def update_order_status(self, order_id: uuid.UUID, new_status: str) -> Order:
        """Update order status with state machine transition validation and stock restoration on cancellation."""
        order = await self.get_order_by_id(order_id)
        valid_targets = self.VALID_STATUS_TRANSITIONS.get(order.status, [])

        if new_status not in valid_targets:
            raise BadRequestException(
                code="INVALID_STATUS_TRANSITION",
                message=f"Cannot transition order from '{order.status}' to '{new_status}'",
            )

        # If transitioning to cancelled, restore stock for items
        if new_status == "cancelled" and order.status != "cancelled":
            for item in order.items:
                try:
                    await self.inventory_service.restore_stock(item.product_id, item.quantity)
                except Exception as e:
                    logger.error(f"Error restoring stock for product {item.product_id} on cancelled order {order.id}: {e}")

        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        await order.save()
        return order

    async def list_user_orders(self, user_id: uuid.UUID) -> List[Order]:
        """List all orders for a given user sorted newest first."""
        return await Order.find(Order.user_id == user_id).sort(-Order.created_at).to_list()
