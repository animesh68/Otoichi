import uuid
from typing import List
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.db.models.user import Address, User
from app.schemas.auth import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
address_router = APIRouter(prefix="/addresses", tags=["Addresses"])


# ==================== AUTH ROUTES ====================

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister):
    """Register a new customer account."""
    auth_service = AuthService()
    user = await auth_service.register(user_in)
    return user


@auth_router.post("/login", response_model=TokenResponse)
async def login(login_in: UserLogin):
    """Authenticate with email and password to receive JWT access and refresh tokens."""
    auth_service = AuthService()
    user = await auth_service.authenticate(login_in)
    return auth_service.generate_tokens(user)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshTokenRequest):
    """Generate new access token using a valid refresh token."""
    auth_service = AuthService()
    return await auth_service.refresh_access_token(req.refresh_token)


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile of currently authenticated user."""
    return current_user


# ==================== ADDRESS ROUTES ====================

@address_router.get("/", response_model=List[AddressResponse])
async def list_my_addresses(current_user: User = Depends(get_current_user)):
    """List all saved shipping addresses for current user."""
    return current_user.addresses


@address_router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    addr_in: AddressCreate,
    current_user: User = Depends(get_current_user),
):
    """Add a new shipping address. Sets default address if marked or if first address."""
    is_first = len(current_user.addresses) == 0
    is_default = addr_in.is_default or is_first

    if is_default:
        for a in current_user.addresses:
            a.is_default = False

    address = Address(
        id=uuid.uuid4(),
        line1=addr_in.line1,
        line2=addr_in.line2,
        city=addr_in.city,
        state=addr_in.state,
        postal_code=addr_in.postal_code,
        country=addr_in.country,
        phone=addr_in.phone,
        is_default=is_default,
    )
    current_user.addresses.append(address)
    await current_user.save()
    return address


@address_router.get("/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    """Get address by ID. Enforces ownership."""
    addr = next((a for a in current_user.addresses if a.id == address_id), None)
    if not addr:
        raise NotFoundException(code="ADDRESS_NOT_FOUND", message="Address not found")
    return addr


@address_router.patch("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: uuid.UUID,
    addr_in: AddressUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update address. Enforces ownership."""
    addr = next((a for a in current_user.addresses if a.id == address_id), None)
    if not addr:
        raise NotFoundException(code="ADDRESS_NOT_FOUND", message="Address not found")

    if addr_in.is_default:
        for a in current_user.addresses:
            a.is_default = False

    update_data = addr_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(addr, field, value)

    await current_user.save()
    return addr


@address_router.delete("/{address_id}", response_model=MessageResponse)
async def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    """Delete address. Enforces ownership."""
    addr = next((a for a in current_user.addresses if a.id == address_id), None)
    if not addr:
        raise NotFoundException(code="ADDRESS_NOT_FOUND", message="Address not found")

    current_user.addresses = [a for a in current_user.addresses if a.id != address_id]
    await current_user.save()
    return MessageResponse(message="Address deleted successfully")
