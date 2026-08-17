import uuid
from typing import Optional
from beanie.odm.operators.update.general import Inc

from app.core.exceptions import InsufficientStockException, NotFoundException
from app.db.models.product import VinylProduct
from app.services.cache_service import cache_service


class InventoryService:
    def __init__(self, db=None):
        self.db = db

    async def verify_stock(self, product_id: uuid.UUID, requested_quantity: int) -> VinylProduct:
        """Read-only check for product availability."""
        product = await VinylProduct.find_one(VinylProduct.id == product_id)
        if not product:
            raise NotFoundException(code="PRODUCT_NOT_FOUND", message=f"Product '{product_id}' not found")

        if product.stock_quantity < requested_quantity:
            raise InsufficientStockException(
                message=f"Only {product.stock_quantity} units available for SKU {product.sku}",
                details={"available_stock": product.stock_quantity, "requested": requested_quantity},
            )

        return product

    async def lock_and_decrement_stock(self, product_id: uuid.UUID, quantity: int) -> VinylProduct:
        """
        Concurrency-safe atomic inventory decrement.
        Uses MongoDB atomic conditional update with $gte condition to prevent race conditions and overselling.
        """
        # First verify product existence
        product = await VinylProduct.find_one(VinylProduct.id == product_id)
        if not product:
            raise NotFoundException(code="PRODUCT_NOT_FOUND", message=f"Product '{product_id}' not found")

        if product.stock_quantity < quantity:
            raise InsufficientStockException(
                message=f"Insufficient stock for SKU {product.sku}. Available: {product.stock_quantity}, Requested: {quantity}",
                details={"available_stock": product.stock_quantity, "requested": quantity, "sku": product.sku},
            )

        # Atomic conditional update
        update_result = await VinylProduct.find_one(
            VinylProduct.id == product_id,
            VinylProduct.stock_quantity >= quantity,
        ).update(Inc({VinylProduct.stock_quantity: -quantity}))

        if not update_result or update_result.modified_count == 0:
            # Re-fetch latest to give accurate available stock error
            refreshed = await VinylProduct.find_one(VinylProduct.id == product_id)
            avail = refreshed.stock_quantity if refreshed else 0
            raise InsufficientStockException(
                message=f"Insufficient stock for SKU {product.sku}. Available: {avail}, Requested: {quantity}",
                details={"available_stock": avail, "requested": quantity, "sku": product.sku},
            )

        # Invalidate cached product and listings
        await cache_service.invalidate_product(product_id)

        # Return updated product
        product.stock_quantity -= quantity
        return product

    async def restore_stock(self, product_id: uuid.UUID, quantity: int) -> None:
        """Restores stock on order cancellation or failure."""
        await VinylProduct.find_one(VinylProduct.id == product_id).update(
            Inc({VinylProduct.stock_quantity: quantity})
        )
        await cache_service.invalidate_product(product_id)
