from datetime import datetime, timezone
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from beanie import Document, Indexed


class Address(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = "US"
    phone: Optional[str] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: Indexed(str, unique=True)
    password_hash: str
    full_name: str
    role: str = "customer"  # "customer", "admin"
    is_active: bool = True
    addresses: List[Address] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
