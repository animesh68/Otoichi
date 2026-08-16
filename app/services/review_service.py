import uuid
from typing import List

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.db.models.order import Order
from app.db.models.product import VinylProduct
from app.db.models.social_and_promo import Review
from app.db.models.user import User
from app.schemas.social_and_promo import ReviewCreate


class ReviewService:
    def __init__(self, db=None):
        self.db = db

    async def create_review(self, user: User, review_in: ReviewCreate) -> Review:
        """
        Create a product review.
        Enforces:
          1. Product exists.
          2. User purchased the product in an order with status == 'delivered'.
          3. User hasn't already submitted a review for this product.
        """
        # 1. Verify product exists
        product = await VinylProduct.find_one(VinylProduct.id == review_in.product_id)
        if not product:
            raise NotFoundException(code="PRODUCT_NOT_FOUND", message="Product does not exist")

        # 2. Check if user already reviewed this product
        existing = await Review.find_one(
            Review.user_id == user.id,
            Review.product_id == review_in.product_id,
        )
        if existing:
            raise ConflictException(
                code="REVIEW_ALREADY_EXISTS",
                message="You have already submitted a review for this product",
            )

        # 3. Verify delivered purchase
        delivered_orders = await Order.find(
            Order.user_id == user.id,
            Order.status == "delivered",
        ).to_list()

        has_purchased = any(
            any(item.product_id == review_in.product_id for item in order.items)
            for order in delivered_orders
        )

        if not has_purchased:
            raise ForbiddenException(
                code="VERIFIED_PURCHASE_REQUIRED",
                message="You can only review products from orders that have been successfully delivered to you",
            )

        # 4. Create review
        review = Review(
            user_id=user.id,
            product_id=review_in.product_id,
            user_name=user.full_name,
            rating=review_in.rating,
            comment=review_in.comment.strip() if review_in.comment else None,
        )
        await review.insert()
        return review

    async def get_product_reviews(self, product_id: uuid.UUID) -> List[Review]:
        """Fetch all reviews for a product."""
        return await Review.find(Review.product_id == product_id).sort(-Review.created_at).to_list()
