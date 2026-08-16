import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.db.models.cart import CartItem
from app.db.models.catalog import Album, Track
from app.db.models.order import Order, OrderItem
from app.db.models.product import VinylProduct
from app.db.models.user import User
from app.services.coupon_service import CouponService
from app.services.inventory_service import InventoryService


class OrderService:
    VALID_STATUS_TRANSITIONS = {
        "pending": ["paid", "cancelled"],
        "paid": ["shipped", "cancelled"],
        "shipped": ["delivered", "cancelled"],
        "delivered": [],  # Terminal state
        "cancelled": [],  # Terminal state
    }

    def __init__(self, db=None):
        self.db = db
        self.inventory_service = InventoryService(db)
        self.coupon_service = CouponService(db)

    async def create_order_from_cart(
        self,
        user: User,
        shipping_address_id: Optional[uuid.UUID] = None,
        shipping_address_data: Optional[Dict[str, Any]] = None,
        coupon_code: Optional[str] = None,
        payment_intent_id: Optional[str] = None,
        status: str = "pending",
    ) -> Order:
        """
        Create a new Order from the user's active cart.
        Locks inventory, snapshots current product prices, and decrements stock.
        """
        cart_items = await CartItem.find(CartItem.user_id == user.id).to_list()
        if not cart_items:
            raise BadRequestException(message="Cannot checkout an empty cart")

        # Resolve address snapshot
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

        # Calculate subtotal and lock stock
        subtotal = 0.0
        order_items_to_create: List[OrderItem] = []

        for item in cart_items:
            locked_product = await self.inventory_service.lock_and_decrement_stock(
                item.product_id, item.quantity
            )
            item_price = float(locked_product.price)
            subtotal += item_price * item.quantity

            title = "Vinyl Item"
            if locked_product.album_id:
                album = await Album.find_one(Album.id == locked_product.album_id)
                if album:
                    title = f"{album.title} ({locked_product.format}, {locked_product.vinyl_variant})"
            elif locked_product.track_id:
                track = await Track.find_one(Track.id == locked_product.track_id)
                if track:
                    title = f"{track.title} ({locked_product.format}, {locked_product.vinyl_variant})"

            order_items_to_create.append(
                OrderItem(
                    id=uuid.uuid4(),
                    product_id=locked_product.id,
                    quantity=item.quantity,
                    unit_price_at_purchase=item_price,
                    product_title_snapshot=title,
                )
            )

        # Apply coupon if provided
        discount_amount = 0.0
        coupon_id = None
        coupon_code_snapshot = None

        if coupon_code:
            coupon, discount_amount = await self.coupon_service.get_and_validate_coupon(
                coupon_code, subtotal, for_update=True
            )
            coupon_id = coupon.id
            coupon_code_snapshot = coupon.code
            await self.coupon_service.increment_coupon_usage(coupon.id)

        shipping_amount = float(settings.FLAT_SHIPPING_RATE)
        total_amount = max(round(subtotal + shipping_amount - discount_amount, 2), 0.0)

        # Create Order
        order = Order(
            user_id=user.id,
            status=status,
            subtotal_amount=round(subtotal, 2),
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency=settings.DEFAULT_CURRENCY,
            shipping_address_snapshot=address_snapshot,
            stripe_payment_intent_id=payment_intent_id,
            coupon_id=coupon_id,
            coupon_code_snapshot=coupon_code_snapshot,
            items=order_items_to_create,
        )
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
        """
        Admin-only status transition update with validation against allowed state transitions.
        If cancelled, restores locked inventory.
        """
        order = await Order.find_one(Order.id == order_id)
        if not order:
            raise NotFoundException(code="ORDER_NOT_FOUND", message="Order not found")

        current_status = order.status
        allowed = self.VALID_STATUS_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            raise BadRequestException(
                code="INVALID_STATUS_TRANSITION",
                message=f"Cannot transition order status from '{current_status}' to '{new_status}'. Allowed transitions: {allowed}",
            )

        # If transitioning to cancelled, restore stock
        if new_status == "cancelled" and current_status != "cancelled":
            for item in order.items:
                if item.product_id:
                    await self.inventory_service.restore_stock(item.product_id, item.quantity)

        order.status = new_status
        await order.save()
        return order
