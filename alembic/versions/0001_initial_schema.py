"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='customer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. Addresses
    op.create_table(
        'addresses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('line1', sa.String(length=255), nullable=False),
        sa.Column('line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False, server_default='United States'),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_addresses_id'), 'addresses', ['id'], unique=False)
    op.create_index(op.f('ix_addresses_user_id'), 'addresses', ['user_id'], unique=False)

    # 3. Artists
    op.create_table(
        'artists',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=1024), nullable=True),
        sa.Column('spotify_artist_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artists_id'), 'artists', ['id'], unique=False)
    op.create_index(op.f('ix_artists_name'), 'artists', ['name'], unique=False)
    op.create_index(op.f('ix_artists_spotify_artist_id'), 'artists', ['spotify_artist_id'], unique=True)

    # 4. Albums
    op.create_table(
        'albums',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('artist_id', sa.Uuid(), nullable=False),
        sa.Column('release_year', sa.Integer(), nullable=True),
        sa.Column('genre', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_art_url', sa.String(length=1024), nullable=True),
        sa.Column('spotify_album_id', sa.String(length=100), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['artist_id'], ['artists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_albums_artist_id'), 'albums', ['artist_id'], unique=False)
    op.create_index(op.f('ix_albums_genre'), 'albums', ['genre'], unique=False)
    op.create_index(op.f('ix_albums_id'), 'albums', ['id'], unique=False)
    op.create_index(op.f('ix_albums_spotify_album_id'), 'albums', ['spotify_album_id'], unique=True)
    op.create_index(op.f('ix_albums_title'), 'albums', ['title'], unique=False)

    # 5. Tracks
    op.create_table(
        'tracks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('album_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('track_number', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('spotify_track_id', sa.String(length=100), nullable=True),
        sa.Column('itunes_preview_url', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tracks_album_id'), 'tracks', ['album_id'], unique=False)
    op.create_index(op.f('ix_tracks_id'), 'tracks', ['id'], unique=False)
    op.create_index(op.f('ix_tracks_spotify_track_id'), 'tracks', ['spotify_track_id'], unique=True)
    op.create_index(op.f('ix_tracks_title'), 'tracks', ['title'], unique=False)

    # 6. Vinyl Products
    op.create_table(
        'vinyl_products',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('product_type', sa.String(length=50), nullable=False),
        sa.Column('album_id', sa.Uuid(), nullable=True),
        sa.Column('track_id', sa.Uuid(), nullable=True),
        sa.Column('format', sa.String(length=50), nullable=False, server_default='LP'),
        sa.Column('vinyl_variant', sa.String(length=50), nullable=False, server_default='standard'),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('is_preorder', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('release_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('image_urls', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('price >= 0', name='check_product_price_non_negative'),
        sa.CheckConstraint('stock_quantity >= 0', name='check_product_stock_non_negative'),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vinyl_products_album_id'), 'vinyl_products', ['album_id'], unique=False)
    op.create_index(op.f('ix_vinyl_products_id'), 'vinyl_products', ['id'], unique=False)
    op.create_index(op.f('ix_vinyl_products_sku'), 'vinyl_products', ['sku'], unique=True)
    op.create_index(op.f('ix_vinyl_products_track_id'), 'vinyl_products', ['track_id'], unique=False)

    # 7. Cart Items
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('(user_id IS NOT NULL) OR (session_id IS NOT NULL)', name='check_cart_owner_present'),
        sa.CheckConstraint('quantity > 0', name='check_cart_quantity_positive'),
        sa.ForeignKeyConstraint(['product_id'], ['vinyl_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'product_id', name='uq_cart_session_product'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product')
    )
    op.create_index(op.f('ix_cart_items_id'), 'cart_items', ['id'], unique=False)
    op.create_index(op.f('ix_cart_items_product_id'), 'cart_items', ['product_id'], unique=False)
    op.create_index(op.f('ix_cart_items_session_id'), 'cart_items', ['session_id'], unique=False)
    op.create_index(op.f('ix_cart_items_user_id'), 'cart_items', ['user_id'], unique=False)

    # 8. Coupons
    op.create_table(
        'coupons',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('times_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('times_used >= 0', name='check_coupon_times_used_non_negative'),
        sa.CheckConstraint('value >= 0', name='check_coupon_value_non_negative'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coupons_code'), 'coupons', ['code'], unique=True)
    op.create_index(op.f('ix_coupons_id'), 'coupons', ['id'], unique=False)

    # 9. Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('subtotal_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.0'),
        sa.Column('shipping_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.0'),
        sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.0'),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('shipping_address_id', sa.Uuid(), nullable=True),
        sa.Column('shipping_address_snapshot', sa.JSON(), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('coupon_id', sa.Uuid(), nullable=True),
        sa.Column('coupon_code_snapshot', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('total_amount >= 0', name='check_order_total_non_negative'),
        sa.ForeignKeyConstraint(['coupon_id'], ['coupons.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['shipping_address_id'], ['addresses.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_stripe_payment_intent_id'), 'orders', ['stripe_payment_intent_id'], unique=True)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)

    # 10. Order Items
    op.create_table(
        'order_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('order_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price_at_purchase', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('product_title_snapshot', sa.String(length=255), nullable=True),
        sa.CheckConstraint('quantity > 0', name='check_order_item_quantity_positive'),
        sa.CheckConstraint('unit_price_at_purchase >= 0', name='check_order_item_price_non_negative'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['vinyl_products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_product_id'), 'order_items', ['product_id'], unique=False)

    # 11. Wishlists
    op.create_table(
        'wishlists',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['vinyl_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_wishlist_user_product')
    )
    op.create_index(op.f('ix_wishlists_id'), 'wishlists', ['id'], unique=False)
    op.create_index(op.f('ix_wishlists_product_id'), 'wishlists', ['product_id'], unique=False)
    op.create_index(op.f('ix_wishlists_user_id'), 'wishlists', ['user_id'], unique=False)

    # 12. Reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_review_rating_range'),
        sa.ForeignKeyConstraint(['product_id'], ['vinyl_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_review_user_product')
    )
    op.create_index(op.f('ix_reviews_id'), 'reviews', ['id'], unique=False)
    op.create_index(op.f('ix_reviews_product_id'), 'reviews', ['product_id'], unique=False)
    op.create_index(op.f('ix_reviews_user_id'), 'reviews', ['user_id'], unique=False)

    # 13. Stock Notifications
    op.create_table(
        'stock_notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('product_id', sa.Uuid(), nullable=False),
        sa.Column('notified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['vinyl_products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', 'product_id', name='uq_stock_notification_email_product')
    )
    op.create_index(op.f('ix_stock_notifications_email'), 'stock_notifications', ['email'], unique=False)
    op.create_index(op.f('ix_stock_notifications_id'), 'stock_notifications', ['id'], unique=False)
    op.create_index(op.f('ix_stock_notifications_product_id'), 'stock_notifications', ['product_id'], unique=False)

    # 14. Stripe Webhook Events (Idempotency)
    op.create_table(
        'stripe_webhook_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stripe_webhook_events_event_id'), 'stripe_webhook_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_stripe_webhook_events_id'), 'stripe_webhook_events', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('stripe_webhook_events')
    op.drop_table('stock_notifications')
    op.drop_table('reviews')
    op.drop_table('wishlists')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('coupons')
    op.drop_table('cart_items')
    op.drop_table('vinyl_products')
    op.drop_table('tracks')
    op.drop_table('albums')
    op.drop_table('artists')
    op.drop_table('addresses')
    op.drop_table('users')
