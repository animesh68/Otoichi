import uuid
from typing import Optional
from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.core.security import decode_token
from app.db.models.user import User

# Security scheme for FastAPI OpenAPI docs
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> User:
    """Extract and validate JWT access token to return current active user."""
    if not auth or not auth.credentials:
        raise UnauthorizedException(message="Authentication token is missing")

    token = auth.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(message="Authentication token has expired")
    except (jwt.InvalidTokenError, Exception):
        raise UnauthorizedException(message="Invalid authentication token")

    if payload.get("type") != "access":
        raise UnauthorizedException(message="Invalid token type (access token required)")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(message="Invalid token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(message="Invalid user identifier format")

    user = await User.find_one(User.id == user_id)

    if not user:
        raise NotFoundException(code="USER_NOT_FOUND", message="User account not found")

    if not user.is_active:
        raise ForbiddenException(message="User account is deactivated")

    return user


async def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[User]:
    """Optionally returns the current user if a valid bearer token is provided."""
    if not auth or not auth.credentials:
        return None

    try:
        payload = decode_token(auth.credentials)
        if payload.get("type") != "access":
            return None
        user_id = uuid.UUID(payload.get("sub"))
        user = await User.find_one(User.id == user_id)
        if user and user.is_active:
            return user
    except Exception:
        return None

    return None


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure that the authenticated user is an administrator."""
    if current_user.role != "admin":
        raise ForbiddenException(code="ADMIN_REQUIRED", message="Admin privileges required")
    return current_user


def get_guest_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None),
) -> Optional[str]:
    """Extract guest cart session ID from header or query param."""
    return x_session_id or session_id
