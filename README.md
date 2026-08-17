# Otoichi (音市)

> A full-stack vinyl record marketplace engineered for music discovery, streaming audio previews, and idempotent Stripe payment fulfillment.

[![Live Demo](https://img.shields.io/badge/Live_Demo-otoichi.vercel.app-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://otoichi.vercel.app/)
[![API Docs](https://img.shields.io/badge/Swagger_Docs-otoichi.onrender.com-468B62?style=for-the-badge&logo=swagger&logoColor=white)](https://otoichi.onrender.com/docs)
[![GitHub](https://img.shields.io/badge/GitHub-animesh68%2FOtoichi-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/animesh68/Otoichi)

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_19-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe_SDK-626CD9?style=flat-square&logo=stripe&logoColor=white)
![JWT](https://img.shields.io/badge/JWT_Auth-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)

---

### Quick Links
* **Live Web Application (Vercel)**: [https://otoichi.vercel.app/](https://otoichi.vercel.app/)
* **Interactive API Documentation (Swagger)**: [https://otoichi.onrender.com/docs](https://otoichi.onrender.com/docs)
* **Backend REST API (Render)**: [https://otoichi.onrender.com/api/v1](https://otoichi.onrender.com/api/v1)
* **GitHub Repository**: [https://github.com/animesh68/Otoichi](https://github.com/animesh68/Otoichi)

---

## Visual Showcase

### Marketplace Home & 3D Coverflow Hero
![Otoichi Home](./shot/home.png)

### Crate Browsing & Goldmine Grading
![Browse & Filters](./shot/browse.png)

### Master Pressing Details & Side A / Side B Tracklist
![Product Detail](./shot/shop_album.png)

### Persistent 30-Second Streamable Audio Preview
![Audio Player](./shot/track_preview.png)

---

## 1. Overview

**Otoichi (音市)** is a full-stack ecommerce marketplace designed for audiophiles and vinyl collectors. The platform bridges physical crate-digging aesthetics with modern, production-grade web architecture.

Key platform characteristics:
* **Rich Storefront & Audio Discovery**: 3D perspective Coverflow carousel, Goldmine standard grading inspection (Mint, Near Mint, Very Good Plus), vinyl variant badges (180g virgin vinyl, 45 RPM 7" singles, 12" LPs), and streamable 30-second audio previews synchronized with Spotify and Apple iTunes APIs.
* **Service-Oriented Backend**: Async FastAPI application backed by MongoDB Atlas and Beanie ODM, enforcing strict domain boundaries across authentication, catalog indexing, cart synchronization, coupon validation, inventory locks, and order management.
* **Authoritative Payment Architecture**: Official Stripe React Elements integration with server-authoritative price recalculations, PaymentIntent generation with idempotency keys, and asynchronous webhook-driven order fulfillment.

---

## 2. Engineering Highlights

* **Stripe Webhook as the Authoritative Fulfillment Engine**: Payments are never fulfilled directly from client-side state. The backend listens for `payment_intent.succeeded` events, verifies HMAC signatures using raw request payload bytes, deduplicates deliveries using a persistent `StripeWebhookEvent` collection, and commits inventory decrements idempotently.
* **Zero-Trust Pricing Calculation**: Subtotals, coupon discounts, and shipping tiers are calculated server-side from the active database. Client-sent prices and totals are discarded. Free shipping is automatically applied for orders exceeding `$100.00`, with unified flat-rate courier shipping applied otherwise.
* **Promotional Zero-Total Order Handling**: When promotional coupons yield a 100% discount, the system bypasses Stripe PaymentIntent creation entirely and routes through a dedicated `zero-total-order` transaction to prevent invalid `$0.00` payment charges.
* **Concurrency-Safe Inventory Management**: Stock decrements use MongoDB atomic conditional updates (`$gte`) to prevent race conditions and overselling during simultaneous checkout attempts. Cancelled orders automatically restore reserved quantities.
* **Clean State Separation**: Explicit separation between order lifecycle states (`pending`, `paid`, `processing`, `shipped`, `delivered`, `cancelled`, `refunded`) and payment provider states (`requires_payment_method`, `requires_confirmation`, `requires_action`, `processing`, `succeeded`, `failed`, `cancelled`, `refunded`, `partially_refunded`).
* **Dual-Source Music Metadata Ingestion**: Ingests master catalog metadata (album art, ISRCs, release years, tracklists) via the Spotify Web API (Client Credentials flow) and pairs each track with 30-second playable AAC preview streams from the Apple iTunes Search API.
* **Custom Themed Stripe Elements**: Embedded Stripe Payment Elements customized via Stripe's Appearance API to match Otoichi's dark lacquer (`#1C1814`), warm ivory (`#F3ECDD`), and brass (`#C89B3C`) design tokens.

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (React 19 + Vite)"]
        UI[Storefront UI]
        AudioCtx[AudioContext Preview Player]
        CartCtx[CartContext]
        StripeElem[Stripe Payment Element]
    end

    subgraph Gateway ["API & Router Layer (FastAPI)"]
        Router[REST API v1 Router]
        AuthMW[JWT Auth Middleware & RBAC]
        SigVerify[Stripe Signature Verification]
    end

    subgraph Services ["Service Layer"]
        AuthSvc[AuthService]
        CatalogSvc[Catalog & Sync Service]
        CartSvc[CartService]
        OrderSvc[OrderService]
        InvSvc[InventoryService]
        PaySvc[PaymentService]
        CouponSvc[CouponService]
    end

    subgraph Data ["Persistence (MongoDB Atlas / Beanie ODM)"]
        Users[(Users & Addresses)]
        CatalogDB[(Albums, Tracks, Artists)]
        ProductsDB[(Vinyl Products & Stock)]
        OrdersDB[(Orders & OrderItems)]
        WebhooksDB[(StripeWebhookEvents)]
    end

    subgraph External ["External Services"]
        Spotify[Spotify Web API]
        iTunes[Apple iTunes Search API]
        StripeAPI[Stripe Payment Gateway]
    end

    UI --> Router
    StripeElem --> StripeAPI
    Router --> AuthMW
    Router --> SigVerify
    AuthMW --> AuthSvc
    SigVerify --> PaySvc

    Router --> CatalogSvc
    Router --> CartSvc
    Router --> OrderSvc
    Router --> CouponSvc

    CatalogSvc --> Spotify
    CatalogSvc --> iTunes
    PaySvc --> StripeAPI

    OrderSvc --> InvSvc
    OrderSvc --> CouponSvc

    AuthSvc --> Users
    CatalogSvc --> CatalogDB
    InvSvc --> ProductsDB
    OrderSvc --> OrdersDB
    PaySvc --> WebhooksDB
```

---

## 4. Payment & Order Fulfillment Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant Frontend as React Frontend
    participant Backend as FastAPI Server
    participant Stripe as Stripe Gateway
    participant Database as MongoDB Atlas

    Customer->>Frontend: Click "Proceed to Checkout"
    Frontend->>Backend: POST /api/v1/checkout/summary (Cart + Coupon)
    Backend->>Database: Query current product prices & stock availability
    Backend-->>Frontend: Authoritative Summary (Subtotal, Discount, Shipping, Total)
    
    Frontend->>Backend: POST /api/v1/checkout/create-intent
    Backend->>Database: Insert Pending Order (status='pending', payment_status='requires_payment_method')
    Backend->>Stripe: stripe.PaymentIntent.create(amount, currency, idempotency_key, metadata)
    Stripe-->>Backend: Return PaymentIntent (id, client_secret)
    Backend->>Database: Link stripe_payment_intent_id to Order
    Backend-->>Frontend: Return client_secret & authoritative totals
    
    Frontend->>Frontend: Mount Stripe Elements (<PaymentElement />)
    Customer->>Frontend: Enter Card Details & Submit Payment
    Frontend->>Stripe: stripe.confirmPayment({ elements, return_url })
    
    alt 3D Secure / SCA Required
        Stripe-->>Customer: Present 3DS Authentication Modal
        Customer->>Stripe: Complete Biometric / OTP Challenge
    end

    Stripe-->>Frontend: Payment status: 'succeeded' / 'processing'
    
    Note over Stripe,Backend: Asynchronous Authoritative Webhook
    Stripe->>Backend: POST /api/v1/webhooks/stripe (payment_intent.succeeded)
    Backend->>Backend: Verify Stripe signature using raw request bytes
    Backend->>Database: Check StripeWebhookEvent (deduplication check)
    
    alt Event Not Yet Processed
        Backend->>Database: Log event_id in StripeWebhookEvent
        Backend->>Database: Atomic conditional stock decrement (stock >= qty)
        Backend->>Database: Increment coupon usage counter
        Backend->>Database: Update Order (status='paid', payment_status='succeeded', paid_at=now)
        Backend->>Database: Clear User Cart
    end
    
    Backend-->>Stripe: HTTP 200 OK {"received": true}
    Frontend->>Customer: Navigate to /order-success (Display real Order Reference & Status)
```

---

## 5. Data Model

The domain layer is structured using Beanie Document models with indexes on queried and relational fields:

```mermaid
erDiagram
    USER ||--o{ ADDRESS : has
    USER ||--o{ ORDER : places
    USER ||--o{ CART_ITEM : owns
    USER ||--o{ REVIEW : writes
    USER ||--o{ WISHLIST : saves

    ARTIST ||--o{ ALBUM : creates
    ARTIST ||--o{ TRACK : performs
    ALBUM ||--o{ TRACK : contains
    ALBUM ||--o{ VINYL_PRODUCT : "pressed as"
    TRACK ||--o{ VINYL_PRODUCT : "pressed as (7-inch single)"

    ORDER ||--|{ ORDER_ITEM : includes
    VINYL_PRODUCT ||--o{ ORDER_ITEM : "purchased in"
    VINYL_PRODUCT ||--o{ CART_ITEM : "added to"
    COUPON ||--o{ ORDER : "applied to"

    USER {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        string role "customer | admin"
        datetime created_at
    }

    VINYL_PRODUCT {
        uuid id PK
        string product_type "album | single"
        uuid album_id FK
        uuid track_id FK
        string format "7-inch | 12-inch | LP | EP"
        string vinyl_variant "standard | colored | splatter"
        float price
        int stock_quantity
        string sku UK
    }

    ORDER {
        uuid id PK
        uuid user_id FK
        string status "pending | paid | processing | shipped | delivered | cancelled"
        string payment_status "requires_payment_method | processing | succeeded | failed"
        float subtotal_amount
        float shipping_amount
        float discount_amount
        float total_amount
        string stripe_payment_intent_id UK
        string checkout_id
        datetime paid_at
        datetime created_at
    }

    COUPON {
        uuid id PK
        string code UK
        string discount_type "percent | fixed"
        float value
        int usage_limit
        int times_used
        bool is_active
    }
```

---

## 6. API Overview

The backend exposes a fully typed RESTful API under the `/api/v1` prefix. Interactive Swagger UI is available at `/docs`.

| Module | Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | `POST` | `/api/v1/auth/register` | Create customer account | No |
| | `POST` | `/api/v1/auth/login` | Authenticate & retrieve JWT access token | No |
| | `POST` | `/api/v1/auth/refresh` | Rotate access token via refresh token | No |
| | `GET` | `/api/v1/auth/me` | Fetch authenticated user profile & addresses | Yes (Customer) |
| **Products & Catalog** | `GET` | `/api/v1/products/` | Filter products by genre, format, price, stock, query | No |
| | `GET` | `/api/v1/products/{id}` | Retrieve individual vinyl product details | No |
| | `GET` | `/api/v1/albums/` | List all curated vinyl albums | No |
| | `GET` | `/api/v1/albums/{id}` | Retrieve album tracklist & associated pressings | No |
| **Cart** | `GET` | `/api/v1/cart/` | Get active cart items and subtotal | Yes (Session/JWT) |
| | `POST` | `/api/v1/cart/items` | Add product to cart with quantity validation | Yes (Session/JWT) |
| | `PUT` | `/api/v1/cart/items/{id}`| Update cart item quantity | Yes (Session/JWT) |
| | `DELETE`| `/api/v1/cart/items/{id}`| Remove item from cart | Yes (Session/JWT) |
| **Checkout & Payments**| `POST` | `/api/v1/checkout/summary` | Get authoritative server pricing calculation | Yes (Customer) |
| | `POST` | `/api/v1/checkout/create-intent` | Initialize Stripe PaymentIntent & client secret | Yes (Customer) |
| | `POST` | `/api/v1/checkout/zero-total-order` | Complete 100% coupon promotional order | Yes (Customer) |
| | `POST` | `/api/v1/checkout/direct-order` | Internal direct order creation (test mode) | Yes (Customer) |
| **Webhooks** | `POST` | `/api/v1/webhooks/stripe` | Authoritative Stripe event handler (HMAC signature) | No (Stripe Sig) |
| **Orders** | `GET` | `/api/v1/orders/` | List customer order history | Yes (Customer) |
| | `GET` | `/api/v1/orders/{id}` | Get detailed order snapshot & items | Yes (Customer) |
| **Coupons & Promo** | `POST` | `/api/v1/coupons/validate` | Validate coupon code against cart subtotal | No |
| **Newsletter (Resend)**| `POST` | `/api/v1/newsletter/subscribe` | Subscribe email to weekly editorial dispatch | No |
| | `POST` | `/api/v1/newsletter/unsubscribe` | Secure one-click unsubscribe via signed token | No |
| | `POST` | `/api/v1/newsletter/trigger-weekly` | Idempotent Monday campaign scheduler job | Yes (`CRON_SECRET` / Admin) |
| **Admin** | `GET` | `/api/v1/admin/metrics` | System sales, revenue, and inventory analytics | Yes (Admin) |
| | `GET` | `/api/v1/admin/cache/metrics` | Real-time Redis/Memory cache telemetry & hit ratios | Yes (Admin) |
| | `POST` | `/api/v1/admin/cache/flush` | Invalidate all cached data on demand | Yes (Admin) |
| | `GET` | `/api/v1/admin/newsletter/metrics` | Newsletter subscribers & campaign analytics | Yes (Admin) |
| | `GET` | `/api/v1/admin/newsletter/subscribers` | Paginated subscriber management list | Yes (Admin) |
| | `GET` | `/api/v1/admin/newsletter/campaigns` | History of dispatched weekly issues | Yes (Admin) |
| | `PATCH` | `/api/v1/admin/orders/{id}/status`| Update order status with transition validation | Yes (Admin) |
| | `POST` | `/api/v1/admin/sync/spotify`| Trigger Spotify/iTunes metadata sync pipeline | Yes (Admin) |

---

## 7. Tech Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend Framework** | React 19 + Vite 8 | Single Page Application with client-side routing, route-level code splitting |
| **Frontend Routing** | React Router v7 | Dynamic product, category, cart, checkout, and unsubscribe routing |
| **Payment UI** | `@stripe/react-stripe-js` | Stripe Payment Elements with custom theme (lazy-loaded) |
| **Styling** | Vanilla CSS Design Tokens | HSL-tailored palette, brass accents, glassmorphism, responsive grid |
| **Icons & Visuals** | Lucide React + Canvas Confetti | Vector icons and interactive celebration feedback |
| **Backend Framework** | FastAPI (Python 3.12+) | Asynchronous ASGI REST API framework |
| **Database & ODM** | MongoDB Atlas + Beanie ODM | Document database with Motor async driver and batched subdocument resolution |
| **Caching Layer** | Upstash Redis + MemoryCache | Cache-aside architecture with deterministic keys, TTLs, targeted invalidation, and graceful offline fallback |
| **Authentication** | JWT (PyJWT) + Passlib (Bcrypt) | Short-lived access tokens (1h) + Refresh tokens (7d) |
| **Payment Gateway** | Stripe Python SDK | PaymentIntents, Webhook signature verification, SCA/3DS |
| **Email & Newsletter** | Resend API + Jinja/HTML | Editorial weekly dispatch ("Letters from the Listening Room"), tamper-proof signed unsubscribe tokens |
| **External APIs** | Spotify Web API + Apple iTunes API | Album art, track metadata, and 30-second audio stream ingestion with response caching |
| **Scheduler** | Vercel Cron / Serverless | Automated Monday 09:00 UTC dispatch with ISO week database-level idempotency |
| **Testing** | Pytest + `pytest-asyncio` + HTTPX | Automated test suite covering auth, cart, payments, webhooks, newsletter, cache (50 tests) |

---

## 8. Project Structure

```text
Otoichi/
├── app/
│   ├── main.py                     # FastAPI application factory, CORS, exception handlers
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings environment configuration
│   │   ├── security.py             # Bcrypt hashing & PyJWT token management
│   │   ├── exceptions.py           # Domain exception classes & error schema handlers
│   │   └── dependencies.py         # DB session, auth providers (get_current_user, require_admin)
│   ├── db/
│   │   ├── mongo.py                # Motor client initialization & Beanie document registration
│   │   └── models/                 # Beanie documents (User, Order, VinylProduct, Album, Track, etc.)
│   ├── schemas/                    # Pydantic request validation and response DTO schemas
│   ├── services/                   # Encapsulated domain business logic:
│   │   ├── auth_service.py         # Registration, authentication, token rotation
│   │   ├── cart_service.py         # Authenticated & guest cart operations
│   │   ├── coupon_service.py       # Discount calculation & usage limits
│   │   ├── inventory_service.py    # Atomic stock decrement and cancellation restoration
│   │   ├── itunes_service.py       # Apple iTunes 30s preview retrieval
│   │   ├── order_service.py        # Order creation, authoritative pricing, state machine
│   │   ├── payment_service.py      # Stripe SDK client & webhook signature verification
│   │   ├── review_service.py       # Verified purchaser review enforcement
│   │   ├── spotify_service.py      # Spotify Web API client (Client Credentials)
│   │   └── sync_service.py         # Catalog sync coordinator
│   └── api/
│       └── v1/                     # Version 1 API route controllers
├── frontend/
│   ├── src/
│   │   ├── api/                    # API client layer & Stripe loader
│   │   ├── components/             # Reusable UI components (CoverflowHero, AudioPlayerBar, StripeCheckoutForm)
│   │   ├── context/                # React Contexts (AudioContext, CartContext, AuthContext)
│   │   ├── pages/                  # Route views (HomePage, BrowsePage, ProductDetailPage, CheckoutPage, etc.)
│   │   ├── utils/                  # Product display normalizers
│   │   ├── App.jsx                 # Application layout and global audio bar
│   │   └── index.css               # Global design tokens and animations
│   ├── package.json
│   └── vite.config.js
├── scripts/                        # Database seeding and metadata sync automation scripts
├── shot/                           # High-resolution application screenshots
├── tests/                          # Automated Pytest suite (34 test cases)
├── .env.example                    # Environment variable template
├── requirements.txt                # Python backend dependencies
└── README.md
```

---

## 9. Local Development Setup

### Prerequisites
* Python 3.12+
* Node.js 18+ and npm
* MongoDB Atlas instance or local MongoDB server (`mongodb://localhost:27017`)
* Stripe developer account (for test API keys)

---

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/animesh68/Otoichi.git
   cd Otoichi
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows:
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Fill in your `DATABASE_URL`, `JWT_SECRET`, and Stripe test credentials.

5. **Start the FastAPI server**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   API docs will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Configure Frontend Environment Variables (Optional)**:
   Create `frontend/.env.local`:
   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
   VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
   ```

4. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   Frontend will be live at: [http://127.0.0.1:5173/](http://127.0.0.1:5173/)

---

## 10. Stripe Development & Webhook Setup

To test live asynchronous payment fulfillment locally:

1. Obtain your Stripe test keys (`pk_test_...` and `sk_test_...`) from the [Stripe Dashboard](https://dashboard.stripe.com/apikeys).
2. Install the [Stripe CLI](https://stripe.com/docs/stripe-cli).
3. Authenticate the CLI:
   ```bash
   stripe login
   ```
4. Forward incoming webhook events to your local FastAPI backend:
   ```bash
   stripe listen --forward-to 127.0.0.1:8000/api/v1/webhooks/stripe
   ```
5. Copy the printed webhook signing secret (`whsec_...`) into your backend `.env`:
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
   ```
6. Trigger a test event:
   ```bash
   stripe trigger payment_intent.succeeded
   ```

---

## 11. Upstash Redis Caching & Deployment

Otoichi utilizes a resilient **Cache-Aside Architecture** with **Upstash Redis** (or Redis Cloud) for low-latency catalog caching, with automatic in-memory fallback if Redis is unconfigured or offline.

### How to Connect Upstash Redis:
1. Create a free account at [https://upstash.com](https://upstash.com).
2. Create a new **Redis** database (select your preferred region, e.g., US East / EU Central).
3. Copy the **Redis URL** (`rediss://default:YOUR_PASSWORD@...upstash.io:6379`).
4. Set backend environment variables on Render:
   * `REDIS_URL=rediss://default:...@...upstash.io:6379`
   * `CACHE_ENABLED=true`
5. Verify cache telemetry via the admin endpoint `GET /api/v1/admin/cache/metrics` or flush with `POST /api/v1/admin/cache/flush`.

---

## 12. Automated Testing

The backend includes a comprehensive test suite written with `pytest` and `pytest-asyncio` covering authentication, catalog N+1 batching, cart/checkout, Stripe webhooks, Resend newsletter, and Redis caching (50 passing tests).

```bash
# Run all test suites
pytest tests/ -v
```

### Test Coverage Highlights
* **Authentication**: Registration, duplicate email rejection, JWT creation, token refresh, admin RBAC guards.
* **Cart Operations**: Session carting, authenticated user cart persistence, stock limit boundary enforcement, guest-to-user cart merging.
* **Checkout & Pricing**: Authoritative price calculation, coupon discounts, free shipping thresholds, zero-total promotional order paths.
* **Stripe Webhooks & Idempotency**: Signature verification on raw payload bytes, duplicate event rejection (`already_processed`), stock decrementing on `payment_intent.succeeded`.
* **Inventory Consistency**: Concurrency-safe atomic decrements, oversell rejection (`InsufficientStockException`), inventory restoration on cancelled orders.
* **Integrations**: Spotify URI parsing, iTunes preview normalization, graceful fallback when metadata is partially missing.

---

## 12. Technical Challenges & Design Decisions

### 1. Payment-Inventory Race Conditions
* **Problem**: In conventional ecommerce architectures, deducting stock upon PaymentIntent creation causes abandoned carts to lock up inventory. Deducting stock only after payment confirmation risks overselling if stock depleted during customer 3DS verification.
* **Solution**: Otoichi validates stock availability before generating the Stripe PaymentIntent, but only commits the final atomic decrement upon verified receipt of the `payment_intent.succeeded` webhook. Furthermore, atomic conditional updates (`stock_quantity >= requested_quantity`) guarantee that multiple concurrent purchases cannot oversell a vinyl pressing.

### 2. Webhook Event Idempotency
* **Problem**: Stripe's webhook infrastructure guarantees at-least-once delivery. Network retries can result in duplicate webhook deliveries for the same payment intent.
* **Solution**: Inbound events are deduplicated against a persistent `StripeWebhookEvent` collection before execution. If an `event_id` was previously recorded, the server immediately acknowledges with `{"received": true, "status": "already_processed"}` without re-decrementing inventory or re-incrementing coupon counters.

### 3. Dual Catalog Synchronization & Audio Previews
* **Problem**: Spotify Web API provides rich album metadata but does not offer public 30-second audio stream URLs for non-authenticated web clients.
* **Solution**: A dual-provider pipeline was engineered: Spotify provides album artwork, tracklists, and canonical ISRC metadata, while the Apple iTunes Search API provides high-bitrate 30-second AAC preview streams.

---

## 13. Security Practices

* **No Plaintext Passwords**: Passwords are cryptographically salted and hashed using Bcrypt.
* **Zero Card Data on Application Servers**: Otoichi never accepts or logs raw card numbers, expiration dates, or CVC values. All payment credentials enter directly through iframe-isolated Stripe Elements.
* **HMAC Signature Verification**: Stripe webhook endpoints verify cryptographic signatures against `STRIPE_WEBHOOK_SECRET` before processing.
* **Role-Based Authorization**: Administrative endpoints (`/api/v1/admin/*`) require explicit JWT role validation (`role == "admin"`).
* **Sanitized Secrets**: `.env` and sensitive production credentials are strictly excluded from source control via `.gitignore`.

---

## 14. Future Roadmap

- [ ] Automated transactional email notifications (order receipt, shipment tracking number) via Resend / SendGrid.
- [ ] Integration with carrier shipping APIs (EasyPost / Shippo) for live real-time rate calculation and tracking label generation.
- [ ] Direct automated refund processing via Stripe Refund API triggered from the admin dashboard.
- [ ] User review photo uploads with cloud storage integration (AWS S3 / Cloudinary).
- [ ] High-fidelity audio waveforms for track previews using Web Audio API.

---

## 15. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
