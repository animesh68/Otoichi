import uuid
from typing import List
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user, require_admin
from app.core.exceptions import ConflictException, NotFoundException
from app.db.models.product import VinylProduct
from app.db.models.social_and_promo import (
    Coupon,
    Review,
    StockNotification,
    Wishlist,
)
from app.db.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.social_and_promo import (
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    CouponValidateRequest,
    CouponValidateResponse,
    ReviewCreate,
    ReviewResponse,
    StockNotificationCreate,
    StockNotificationResponse,
    WishlistAdd,
    WishlistResponse,
)
from app.services.cart_service import build_product_response
from app.services.coupon_service import CouponService
from app.services.review_service import ReviewService

wishlist_router = APIRouter(prefix="/wishlist", tags=["Wishlist"])
reviews_router = APIRouter(prefix="/reviews", tags=["Reviews"])
coupons_router = APIRouter(prefix="/coupons", tags=["Coupons"])
stock_notifications_router = APIRouter(prefix="/stock-notifications", tags=["Stock Notifications"])


# ==================== WISHLIST ====================

@wishlist_router.get("/", response_model=List[WishlistResponse])
async def list_my_wishlist(current_user: User = Depends(get_current_user)):
    """List all items saved in the authenticated user's wishlist."""
    items = await Wishlist.find(Wishlist.user_id == current_user.id).sort(-Wishlist.created_at).to_list()
    res = []
    for item in items:
        prod = await VinylProduct.find_one(VinylProduct.id == item.product_id)
        prod_resp = await build_product_response(prod) if prod else None
        res.append(
            WishlistResponse(
                id=item.id,
                user_id=item.user_id,
                product_id=item.product_id,
                product=prod_resp,
                created_at=item.created_at,
            )
        )
    return res


@wishlist_router.post("/", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    item_in: WishlistAdd,
    current_user: User = Depends(get_current_user),
):
    """Add a product to the authenticated user's wishlist. Prevents duplicates."""
    prod = await VinylProduct.find_one(VinylProduct.id == item_in.product_id)
    if not prod:
        raise NotFoundException(code="PRODUCT_NOT_FOUND", message="Product does not exist")

    existing = await Wishlist.find_one(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == item_in.product_id,
    )
    if existing:
        raise ConflictException(code="ALREADY_IN_WISHLIST", message="Product is already in your wishlist")

    wishlist_item = Wishlist(
        user_id=current_user.id,
        product_id=item_in.product_id,
    )
    await wishlist_item.insert()

    prod_resp = await build_product_response(prod)
    return WishlistResponse(
        id=wishlist_item.id,
        user_id=wishlist_item.user_id,
        product_id=wishlist_item.product_id,
        product=prod_resp,
        created_at=wishlist_item.created_at,
    )


@wishlist_router.delete("/{product_id}", response_model=MessageResponse)
async def remove_from_wishlist(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    """Remove a product from the authenticated user's wishlist."""
    item = await Wishlist.find_one(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == product_id,
    )
    if not item:
        raise NotFoundException(code="NOT_FOUND_IN_WISHLIST", message="Product is not in your wishlist")

    await item.delete()
    return MessageResponse(message="Product removed from wishlist")


# ==================== REVIEWS ====================

@reviews_router.get("/product/{product_id}", response_model=List[ReviewResponse])
async def list_product_reviews(product_id: uuid.UUID):
    """List all verified reviews for a specific product."""
    review_service = ReviewService()
    return await review_service.get_product_reviews(product_id)


@reviews_router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Submit a review for a product.
    Enforces that user has purchased the product in a delivered order.
    """
    review_service = ReviewService()
    return await review_service.create_review(user=current_user, review_in=review_in)


# ==================== COUPONS ====================

@coupons_router.post("/validate", response_model=CouponValidateResponse)
async def validate_coupon(req: CouponValidateRequest):
    """Validate a coupon code against a subtotal and return the discount amount."""
    coupon_service = CouponService()
    try:
        coupon, discount_amount = await coupon_service.get_and_validate_coupon(
            code=req.code,
            subtotal=req.subtotal,
            for_update=False,
        )
        return CouponValidateResponse(
            valid=True,
            code=coupon.code,
            discount_type=coupon.discount_type,
            value=float(coupon.value),
            discount_amount=discount_amount,
            message="Coupon applied successfully",
        )
    except Exception as e:
        return CouponValidateResponse(
            valid=False,
            code=req.code,
            discount_type="",
            value=0.0,
            discount_amount=0.0,
            message=str(getattr(e, "message", str(e))),
        )


@coupons_router.get("/", response_model=List[CouponResponse])
async def list_coupons(admin: User = Depends(require_admin)):
    """Admin: List all coupons."""
    return await Coupon.find().sort(-Coupon.created_at).to_list()


@coupons_router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    coupon_in: CouponCreate,
    admin: User = Depends(require_admin),
):
    """Admin: Create a new discount coupon."""
    clean_code = coupon_in.code.strip().upper()
    existing = await Coupon.find_one(Coupon.code == clean_code)
    if existing:
        raise ConflictException(code="COUPON_ALREADY_EXISTS", message="Coupon code already exists")

    coupon = Coupon(
        code=clean_code,
        discount_type=coupon_in.discount_type,
        value=coupon_in.value,
        expires_at=coupon_in.expires_at,
        usage_limit=coupon_in.usage_limit,
        is_active=coupon_in.is_active,
    )
    await coupon.insert()
    return coupon


@coupons_router.patch("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: uuid.UUID,
    coupon_in: CouponUpdate,
    admin: User = Depends(require_admin),
):
    """Admin: Update an existing coupon."""
    coupon = await Coupon.find_one(Coupon.id == coupon_id)
    if not coupon:
        raise NotFoundException(code="COUPON_NOT_FOUND", message="Coupon not found")

    update_data = coupon_in.model_dump(exclude_unset=True)
    if "code" in update_data:
        update_data["code"] = update_data["code"].strip().upper()

    for field, value in update_data.items():
        setattr(coupon, field, value)

    await coupon.save()
    return coupon


@coupons_router.delete("/{coupon_id}", response_model=MessageResponse)
async def delete_coupon(
    coupon_id: uuid.UUID,
    admin: User = Depends(require_admin),
):
    """Admin: Delete a coupon."""
    coupon = await Coupon.find_one(Coupon.id == coupon_id)
    if not coupon:
        raise NotFoundException(code="COUPON_NOT_FOUND", message="Coupon not found")

    await coupon.delete()
    return MessageResponse(message="Coupon deleted successfully")


# ==================== STOCK NOTIFICATIONS ====================

@stock_notifications_router.post("/subscribe", response_model=StockNotificationResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_stock_notification(req: StockNotificationCreate):
    """
    Subscribe an email address to receive notifications when an out-of-stock product is restocked.
    Prevents duplicate subscriptions.
    """
    prod = await VinylProduct.find_one(VinylProduct.id == req.product_id)
    if not prod:
        raise NotFoundException(code="PRODUCT_NOT_FOUND", message="Product does not exist")

    email_clean = req.email.strip().lower()
    existing = await StockNotification.find_one(
        StockNotification.email == email_clean,
        StockNotification.product_id == req.product_id,
    )
    if existing:
        return existing

    sub = StockNotification(
        email=email_clean,
        product_id=req.product_id,
        notified=False,
    )
    await sub.insert()
    return sub
