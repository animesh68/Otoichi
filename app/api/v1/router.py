from fastapi import APIRouter

from app.api.v1.admin import admin_router
from app.api.v1.auth import address_router, auth_router
from app.api.v1.cart import cart_router
from app.api.v1.catalog import albums_router, artists_router, tracks_router
from app.api.v1.checkout import checkout_router
from app.api.v1.newsletter import newsletter_router
from app.api.v1.orders import orders_router
from app.api.v1.products import products_router
from app.api.v1.social_and_promo import (
    coupons_router,
    reviews_router,
    stock_notifications_router,
    wishlist_router,
)
from app.api.v1.webhooks import webhooks_router

api_v1_router = APIRouter()

# Register all endpoint groups
api_v1_router.include_router(auth_router)
api_v1_router.include_router(address_router)
api_v1_router.include_router(artists_router)
api_v1_router.include_router(albums_router)
api_v1_router.include_router(tracks_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(checkout_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(wishlist_router)
api_v1_router.include_router(reviews_router)
api_v1_router.include_router(coupons_router)
api_v1_router.include_router(stock_notifications_router)
api_v1_router.include_router(newsletter_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(admin_router)

