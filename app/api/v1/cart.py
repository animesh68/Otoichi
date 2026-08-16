import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_guest_session_id, get_optional_current_user
from app.core.exceptions import UnauthorizedException
from app.db.models.user import User
from app.schemas.cart import (
    CartItemAdd,
    CartItemUpdate,
    CartMergeRequest,
    CartResponse,
)
from app.schemas.common import MessageResponse
from app.services.cart_service import CartService

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


@cart_router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: Optional[User] = Depends(get_optional_current_user),
    session_id: Optional[str] = Depends(get_guest_session_id),
):
    """
    Get current cart items and totals.
    Works for both authenticated users and guest sessions via X-Session-ID.
    """
    cart_service = CartService()
    user_id = current_user.id if current_user else None
    return await cart_service.get_cart(user_id=user_id, session_id=session_id)


@cart_router.post("/items", response_model=CartResponse, status_code=status.HTTP_200_OK)
async def add_item_to_cart(
    item_in: CartItemAdd,
    current_user: Optional[User] = Depends(get_optional_current_user),
    session_id: Optional[str] = Depends(get_guest_session_id),
):
    """
    Add a product to the cart or increase its quantity.
    If guest, provide X-Session-ID header.
    """
    cart_service = CartService()
    user_id = current_user.id if current_user else None
    await cart_service.add_item(
        product_id=item_in.product_id,
        quantity=item_in.quantity,
        user_id=user_id,
        session_id=session_id,
    )
    return await cart_service.get_cart(user_id=user_id, session_id=session_id)


@cart_router.patch("/items/{cart_item_id}", response_model=CartResponse)
async def update_cart_item(
    cart_item_id: uuid.UUID,
    item_in: CartItemUpdate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    session_id: Optional[str] = Depends(get_guest_session_id),
):
    """Update item quantity in cart."""
    cart_service = CartService()
    user_id = current_user.id if current_user else None
    await cart_service.update_item_quantity(
        cart_item_id=cart_item_id,
        quantity=item_in.quantity,
        user_id=user_id,
        session_id=session_id,
    )
    return await cart_service.get_cart(user_id=user_id, session_id=session_id)


@cart_router.delete("/items/{cart_item_id}", response_model=CartResponse)
async def remove_cart_item(
    cart_item_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    session_id: Optional[str] = Depends(get_guest_session_id),
):
    """Remove an item from cart."""
    cart_service = CartService()
    user_id = current_user.id if current_user else None
    await cart_service.remove_item(
        cart_item_id=cart_item_id,
        user_id=user_id,
        session_id=session_id,
    )
    return await cart_service.get_cart(user_id=user_id, session_id=session_id)


@cart_router.delete("/", response_model=MessageResponse)
async def clear_cart(
    current_user: Optional[User] = Depends(get_optional_current_user),
    session_id: Optional[str] = Depends(get_guest_session_id),
):
    """Clear all items in cart."""
    cart_service = CartService()
    user_id = current_user.id if current_user else None
    await cart_service.clear_cart(user_id=user_id, session_id=session_id)
    return MessageResponse(message="Cart cleared successfully")


@cart_router.post("/merge", response_model=CartResponse)
async def merge_guest_cart(
    req: CartMergeRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Merge items from a guest session cart into the authenticated user's cart.
    Requires authentication.
    """
    if not current_user:
        raise UnauthorizedException(message="Authentication required to merge cart")

    cart_service = CartService()
    return await cart_service.merge_guest_cart(req.guest_session_id, current_user.id)
