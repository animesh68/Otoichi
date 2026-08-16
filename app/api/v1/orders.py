import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.db.models.order import Order
from app.db.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderResponse
from app.services.order_service import OrderService

orders_router = APIRouter(prefix="/orders", tags=["Orders"])


@orders_router.get("/", response_model=PaginatedResponse[OrderResponse])
async def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """List orders belonging to the authenticated customer."""
    query = Order.find(Order.user_id == current_user.id)
    total = await query.count()
    items = await query.sort(-Order.created_at).skip((page - 1) * page_size).limit(page_size).to_list()

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@orders_router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of an order. Enforces customer ownership."""
    order_service = OrderService()
    return await order_service.get_order_by_id(order_id=order_id, user=current_user)
