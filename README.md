# Otoichi (音市) — Backend Service

Otoichi is a production-grade online vinyl record marketplace backend built with Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Alembic, Pydantic v2, and Stripe.

---

## 1. Project Overview

Otoichi provides an authoritative, secure, and robust REST API for vinyl record discovery, catalog browsing, cart management (guest and authenticated), Stripe checkout with webhooks, price snapshotting, concurrency-safe inventory decrements, promotional coupons, verified purchaser reviews, and metadata enrichment from Spotify and iTunes.

---

## 2. Architecture

The application follows a clean layered architecture with strict separation of concerns:

```text
app/
├── main.py                     # FastAPI app factory, CORS, exception handlers, and routing
├── core/
│   ├── config.py               # Pydantic BaseSettings environment configuration
│   ├── security.py             # Bcrypt hashing & PyJWT token management (access & refresh)
│   ├── exceptions.py           # Domain exceptions & standard error formatting
│   └── dependencies.py         # DB session, auth (get_current_user, require_admin), guest sessions
├── db/
│   ├── base.py                 # SQLAlchemy DeclarativeBase, UUIDMixin, TimestampMixin
│   ├── session.py              # Async engine & session factory
│   └── models/                 # SQLAlchemy 2.0 models (User, Address, Artist, Album, Track,
│                               # VinylProduct, CartItem, Order, OrderItem, Wishlist, Review,
│                               # Coupon, StockNotification, StripeWebhookEvent)
├── schemas/                    # Pydantic v2 validation models and response DTOs
├── services/                   # Encapsulated business domain services:
│   ├── auth_service.py         # Registration, password validation, token rotation
│   ├── cart_service.py         # Authenticated & guest carts, cart merging
│   ├── inventory_service.py    # Concurrency-safe inventory locking (SELECT FOR UPDATE)
│   ├── order_service.py        # Order lifecycle, frozen price snapshots, status transitions
│   ├── coupon_service.py       # Atomic coupon application and boundary checks
│   ├── payment_service.py      # Abstract payment interface + Stripe implementation
│   ├── review_service.py       # Verified delivered purchase requirement enforcement
│   ├── spotify_service.py      # Spotify Web API client (Client Credentials flow)
│   ├── itunes_service.py       # iTunes Search API client (30s audio previews)
│   └── sync_service.py         # Catalog metadata synchronization pipeline
└── api/
    └── v1/                     # Clean RESTful API version 1 endpoint controllers
```

---

## 3. Technology Stack

- **Language**: Python 3.12+
- **Web Framework**: FastAPI (Async ASGI)
- **Database & ORM**: PostgreSQL with SQLAlchemy 2.0 (`asyncpg` for app, `psycopg` binary)
- **Schema Validation**: Pydantic v2 (`pydantic-settings`)
- **Database Migrations**: Alembic
- **Authentication**: JWT (Short-lived Access Tokens + Long-lived Refresh Tokens) + Bcrypt
- **Payments**: Stripe Test Mode (Payment Intents + Webhooks with signature verification)
- **Integrations**: Spotify Web API (Client Credentials) & Apple iTunes Search API
- **Testing**: Pytest + `pytest-asyncio` + `aiosqlite` in-memory test database
- **Containerization**: Docker & Docker Compose

---

## 4. Requirements & Installation

### Local Prerequisites
- Python 3.12+ (or `uv`)
- PostgreSQL 15+ (or Docker)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd Otoichi
   ```

2. **Create virtual environment and install dependencies**:
   ```bash
   uv venv .venv
   # Windows:
   .venv\Scripts\activate
   uv pip install -r requirements.txt

   # Linux / macOS:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

---

## 5. Running with Docker Compose

To start both PostgreSQL and the FastAPI application in Docker with automatic migration and seeding:

```bash
docker-compose up --build
```

The API will be available at:
`http://localhost:8000`

---

## 6. Database Migrations (Alembic)

Run migrations to bring the database schema up to the latest revision:

```bash
alembic upgrade head
```

To create a new migration:
```bash
alembic revision --autogenerate -m "describe_changes"
```

---

## 7. Database Seeding

Run the seed script to populate initial users, sample discount coupons, and catalog items from `data/seed_data.json`:

```bash
python -m scripts.seed
```

### Seeded Credentials
- **Admin**: `admin@otoichi.com` / `AdminPassword123!`
- **Customer**: `customer@otoichi.com` / `CustomerPassword123!`
- **Coupons**: `VINYL10` (10% off), `SAVE5` ($5.00 off), `VIP20` (20% off)

The seeder is **100% idempotent**; running it repeatedly will never create duplicate artists, albums, tracks, or vinyl products.

---

## 8. Running Automated Tests

Run the complete test suite using pytest:

```bash
pytest -v
```

Tests run against an isolated in-memory async SQLite database, verifying:
- Authentication & JWT token lifecycles
- Role-based authorization & resource ownership checks
- Catalog querying, multi-attribute filtering, sorting, pagination, and derived `low_stock`
- Cart operations, guest session tracking, and guest-to-user cart merging
- Concurrency-safe inventory decrements and oversell prevention
- Stripe PaymentIntent creation, signature verification, and webhook idempotency
- Immutable historical price snapshots in orders
- State transition protections for orders
- Verified delivered purchase requirements for product reviews
- Coupon expiration, usage limits, and negative-total boundary conditions
- Seed script execution and idempotency

---

## 9. API Documentation (Swagger / OpenAPI)

FastAPI provides an interactive OpenAPI / Swagger UI at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 10. Authentication & Authorization Flow

1. **Register**: `POST /api/v1/auth/register` (body: `email`, `password`, `full_name`)
2. **Login**: `POST /api/v1/auth/login` (returns `access_token`, `refresh_token`, `expires_in`)
3. **Authenticated Requests**: Pass header `Authorization: Bearer <access_token>`
4. **Refresh Token**: `POST /api/v1/auth/refresh` (body: `{"refresh_token": "..."}`)
5. **Admin Operations**: Any user with `role: "admin"` can access `/api/v1/admin/*` endpoints.

---

## 11. External Integrations

### Spotify Integration
- Authenticates using **Client Credentials flow** (no Spotify user login required).
- Fetches artist details, album metadata, high-resolution cover art, and complete tracklists with track numbers and durations.
- Admin sync endpoint: `POST /api/v1/admin/sync` accepts Spotify Album/Track IDs or search queries.

### iTunes Audio Previews
- Spotify does not provide full 30s preview MP3s for all tracks.
- When an album or single is imported, `iTunesService` searches `artist + track_title` on `https://itunes.apple.com/search`.
- If an audio preview is found, it is saved in `itunes_preview_url`.
- If no match exists, `itunes_preview_url` is stored as `null` without crashing or interrupting the synchronization.

### Stripe Payments & Webhooks
- `POST /api/v1/checkout/create-intent`: Computes order subtotal, flat-rate shipping ($5.00), and coupon discounts to create a Stripe PaymentIntent in test mode.
- `POST /api/v1/webhooks/stripe`:
  1. Validates `stripe-signature` header using `STRIPE_WEBHOOK_SECRET`.
  2. Ensures idempotency by recording `event_id` in `stripe_webhook_events`. Duplicate deliveries are ignored.
  3. On `payment_intent.succeeded`: Locks stock transactionally, creates the order with price snapshots, marks status `paid`, and increments coupon usage atomically.

---

## 12. Frontend Developer Handoff Guide

When building the Phase 2 frontend, adhere to the following contracts:

### Base URL & Endpoints
- **API Base URL**: `http://localhost:8000/api/v1`
- **Error Format**: All errors return a uniform structure:
  ```json
  {
    "error": {
      "code": "INSUFFICIENT_STOCK",
      "message": "Only 2 units available for SKU VINYL-ALBUM-01",
      "details": { "available_stock": 2, "requested": 5 }
    }
  }
  ```

### Guest vs. Authenticated Carts
- **Guest Users**: Generate a UUID string for the session and pass it in the `X-Session-ID` header on all `/api/v1/cart/*` requests.
- **Login / Register Transition**: After a guest logs in or registers, make a single call to `POST /api/v1/cart/merge` with `{"guest_session_id": "<UUID>"}` to transfer all guest items into their authenticated cart.

### Derived `low_stock` Field
- Products include a computed boolean `low_stock: true` when `stock_quantity <= 5`. Frontend can use this to display *"Only X items left!"* badges without hardcoding inventory thresholds.

### Checkout Flow
1. Call `POST /api/v1/checkout/create-intent` with `{ "coupon_code": "...", "shipping_address_id": "..." }`.
2. Receive `client_secret` and initialize Stripe Elements on the frontend.
3. Confirm payment with Stripe.js using `stripe.confirmCardPayment(client_secret, ...)`.
4. Stripe sends the verified webhook to `/api/v1/webhooks/stripe`, which creates and confirms the order.

---

## 13. Known Limitations & Out of Scope

- **Tax Calculation**: Automated sales tax / VAT calculation is excluded; prices are gross/net as configured.
- **Dynamic Shipping Rates**: Flat-rate shipping ($5.00 default) is applied rather than dynamic carrier rate APIs.
- **Audio Previews**: Audio previews rely on the iTunes Search API (30-second AAC streams) as Spotify deprecated public 30s preview streams.
