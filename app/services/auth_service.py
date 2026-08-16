import uuid
from typing import Optional
import jwt

from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister


class AuthService:
    def __init__(self, db=None):
        self.db = db

    async def register(self, user_in: UserRegister, role: str = "customer") -> User:
        """Register a new user account."""
        email_clean = user_in.email.lower().strip()
        existing = await User.find_one(User.email == email_clean)
        if existing:
            raise ConflictException(
                code="EMAIL_ALREADY_REGISTERED",
                message="An account with this email address already exists",
            )

        user = User(
            email=email_clean,
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name.strip(),
            role=role,
            is_active=True,
        )
        await user.insert()
        return user

    async def authenticate(self, login_in: UserLogin) -> User:
        """Authenticate user credentials."""
        email_clean = login_in.email.lower().strip()
        user = await User.find_one(User.email == email_clean)

        if not user or not verify_password(login_in.password, user.password_hash):
            raise UnauthorizedException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password",
            )

        if not user.is_active:
            raise UnauthorizedException(
                code="ACCOUNT_INACTIVE",
                message="Account has been deactivated",
            )

        return user

    def generate_tokens(self, user: User) -> TokenResponse:
        """Generate JWT access and refresh token pair."""
        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token = create_refresh_token(subject=str(user.id), role=user.role)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Issue new access and refresh tokens using a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(message="Refresh token has expired")
        except Exception:
            raise UnauthorizedException(message="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedException(message="Invalid token type (refresh token required)")

        user_id_str = payload.get("sub")
        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            raise UnauthorizedException(message="Invalid token payload")

        user = await User.find_one(User.id == user_id)

        if not user or not user.is_active:
            raise UnauthorizedException(message="User not found or inactive")

        return self.generate_tokens(user)
