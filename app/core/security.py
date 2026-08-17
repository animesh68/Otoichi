from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived JWT refresh token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": subject,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub", "type"]}
    )


def generate_unsubscribe_token(email: str) -> str:
    """Generate a tamper-proof signed token for secure one-click email unsubscription."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=365)  # 1 year validity
    payload = {
        "sub": email.strip().lower(),
        "type": "unsubscribe",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_unsubscribe_token(token: str) -> Optional[str]:
    """
    Validate an unsubscribe token and return the normalized email address.
    Returns None if token is invalid, expired, or corrupted.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]}
        )
        if payload.get("type") != "unsubscribe":
            return None
        return payload.get("sub", "").strip().lower() or None
    except Exception:
        return None

