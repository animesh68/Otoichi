from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Otoichi Vinyl Marketplace"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database (MongoDB / PostgreSQL)
    DATABASE_URL: str = "mongodb+srv://lovelilori:Yashu2035@cluster0.ml0jzym.mongodb.net/?appName=Cluster0"
    MONGODB_DB_NAME: str = "otoichi"

    # JWT Authentication
    JWT_SECRET: str = "CHANGE_THIS_IN_PRODUCTION_SUPER_SECRET_KEY_1234567890_OTOICHI"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7    # 7 days

    # Spotify Web API
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""

    # Stripe Payments
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_CURRENCY: str = "usd"
    ALLOW_MOCK_PAYMENTS: bool = True

    # Resend Email & Newsletter
    RESEND_API_KEY: str = ""
    NEWSLETTER_FROM_EMAIL: str = "newsletter@otoichi.com"
    NEWSLETTER_FROM_NAME: str = "Otoichi (音市)"
    PUBLIC_APP_URL: str = "https://otoichi.vercel.app"
    CRON_SECRET: str = "otoichi_cron_secret_key_change_me"

    # Business Rules
    LOW_STOCK_THRESHOLD: int = 5
    DEFAULT_CURRENCY: str = "USD"
    FLAT_SHIPPING_RATE: float = 7.50
    FREE_SHIPPING_THRESHOLD: float = 100.00

    # Redis / Upstash Caching
    REDIS_URL: str = ""
    CACHE_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
