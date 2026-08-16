import uuid
from typing import List, Optional

from app.core.exceptions import BadRequestException, InsufficientStockException, NotFoundException
from app.db.models.cart import CartItem
from app.db.models.catalog import Album, Track, Artist
from app.db.models.product import VinylProduct
from app.schemas.cart import CartItemResponse, CartResponse
from app.schemas.catalog import AlbumResponse, ArtistResponse, TrackResponse
from app.schemas.product import ProductResponse


async def build_product_response(product: VinylProduct) -> ProductResponse:
    """Helper to populate AlbumResponse / TrackResponse on ProductResponse."""
    album_resp = None
    track_resp = None

    if product.album_id:
        album = await Album.find_one(Album.id == product.album_id)
        if album:
            artist = await Artist.find_one(Artist.id == album.artist_id)
            artist_name = artist.name if artist else album.artist_name
            artist_resp = ArtistResponse.model_validate(artist) if artist else None
            tracks = await Track.find(Track.album_id == album.id).sort(+Track.track_number).to_list()
            album_resp = AlbumResponse(
                id=album.id,
                title=album.title,
                artist_id=album.artist_id,
                artist_name=artist_name,
                release_year=album.release_year,
                genre=album.genre,
                description=album.description,
                cover_art_url=album.cover_art_url,
                spotify_album_id=album.spotify_album_id,
                label=album.label,
                created_at=album.created_at,
                artist=artist_resp,
                tracks=[TrackResponse.model_validate(t) for t in tracks],
            )

    if product.track_id:
        track = await Track.find_one(Track.id == product.track_id)
        if track:
            artist = await Artist.find_one(Artist.id == track.artist_id) if track.artist_id else None
            track_artist_name = artist.name if artist else getattr(track, "artist_name", None)
            track_resp = TrackResponse(
                id=track.id,
                title=track.title,
                album_id=track.album_id,
                artist_id=track.artist_id,
                artist_name=track_artist_name,
                track_number=track.track_number,
                duration_ms=track.duration_ms,
                spotify_track_id=track.spotify_track_id,
                itunes_preview_url=track.itunes_preview_url,
                created_at=track.created_at,
            )

    return ProductResponse(
        id=product.id,
        product_type=product.product_type,
        album_id=product.album_id,
        track_id=product.track_id,
        format=product.format,
        vinyl_variant=product.vinyl_variant,
        price=product.price,
        currency=product.currency,
        stock_quantity=product.stock_quantity,
        sku=product.sku,
        is_preorder=product.is_preorder,
        release_date=product.release_date,
        image_urls=product.image_urls,
        created_at=product.created_at,
        album=album_resp,
        track=track_resp,
    )


class CartService:
    def __init__(self, db=None):
        self.db = db

    async def get_cart(self, user_id: Optional[uuid.UUID] = None, session_id: Optional[str] = None) -> CartResponse:
        """Fetch all items in the user's or guest's cart with current pricing."""
        if not user_id and not session_id:
            return CartResponse(items=[], total_items=0, subtotal=0.0)

        if user_id:
            cart_items = await CartItem.find(CartItem.user_id == user_id).to_list()
        else:
            cart_items = await CartItem.find(CartItem.session_id == session_id).to_list()

        items_resp: List[CartItemResponse] = []
        subtotal = 0.0
        total_items = 0

        for item in cart_items:
            product = await VinylProduct.find_one(VinylProduct.id == item.product_id)
            if not product:
                continue

            prod_resp = await build_product_response(product)
            item_subtotal = float(product.price) * item.quantity
            subtotal += item_subtotal
            total_items += item.quantity

            items_resp.append(
                CartItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product=prod_resp,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )

        return CartResponse(
            items=items_resp,
            total_items=total_items,
            subtotal=round(subtotal, 2),
            currency="USD",
        )

    async def add_item(
        self,
        product_id: uuid.UUID,
        quantity: int,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
    ) -> CartItem:
        """Add a product to cart or increase its quantity if already present."""
        if not user_id and not session_id:
            raise BadRequestException(message="User authentication or session ID is required to manage cart")

        if quantity <= 0:
            raise BadRequestException(message="Quantity must be greater than zero")

        product = await VinylProduct.find_one(VinylProduct.id == product_id)
        if not product:
            raise NotFoundException(code="PRODUCT_NOT_FOUND", message="Product does not exist")

        if user_id:
            cart_item = await CartItem.find_one(CartItem.user_id == user_id, CartItem.product_id == product_id)
        else:
            cart_item = await CartItem.find_one(CartItem.session_id == session_id, CartItem.product_id == product_id)

        target_quantity = quantity if not cart_item else (cart_item.quantity + quantity)

        if product.stock_quantity < target_quantity:
            raise InsufficientStockException(
                message=f"Cannot add {quantity} more. Total requested ({target_quantity}) exceeds available stock ({product.stock_quantity})",
                details={"available_stock": product.stock_quantity, "requested_total": target_quantity},
            )

        if cart_item:
            cart_item.quantity = target_quantity
            await cart_item.save()
        else:
            cart_item = CartItem(
                user_id=user_id,
                session_id=session_id if not user_id else None,
                product_id=product_id,
                quantity=quantity,
            )
            await cart_item.insert()

        return cart_item

    async def update_item_quantity(
        self,
        cart_item_id: uuid.UUID,
        quantity: int,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
    ) -> CartItem:
        """Update the quantity of a specific cart item."""
        if quantity <= 0:
            raise BadRequestException(message="Quantity must be greater than zero")

        if user_id:
            cart_item = await CartItem.find_one(CartItem.id == cart_item_id, CartItem.user_id == user_id)
        else:
            cart_item = await CartItem.find_one(CartItem.id == cart_item_id, CartItem.session_id == session_id)

        if not cart_item:
            raise NotFoundException(code="CART_ITEM_NOT_FOUND", message="Cart item not found")

        product = await VinylProduct.find_one(VinylProduct.id == cart_item.product_id)
        if product and product.stock_quantity < quantity:
            raise InsufficientStockException(
                message=f"Requested quantity ({quantity}) exceeds available stock ({product.stock_quantity})"
            )

        cart_item.quantity = quantity
        await cart_item.save()
        return cart_item

    async def remove_item(
        self,
        cart_item_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Remove an item from cart."""
        if user_id:
            cart_item = await CartItem.find_one(CartItem.id == cart_item_id, CartItem.user_id == user_id)
        else:
            cart_item = await CartItem.find_one(CartItem.id == cart_item_id, CartItem.session_id == session_id)

        if not cart_item:
            raise NotFoundException(code="CART_ITEM_NOT_FOUND", message="Cart item not found")

        await cart_item.delete()

    async def clear_cart(self, user_id: Optional[uuid.UUID] = None, session_id: Optional[str] = None) -> None:
        """Clear all items in cart."""
        if user_id:
            await CartItem.find(CartItem.user_id == user_id).delete()
        elif session_id:
            await CartItem.find(CartItem.session_id == session_id).delete()

    async def merge_guest_cart(self, guest_session_id: str, user_id: uuid.UUID) -> CartResponse:
        """
        Merge guest cart items into authenticated user cart.
        Combines quantities for duplicate products up to available stock.
        """
        guest_items = await CartItem.find(CartItem.session_id == guest_session_id).to_list()
        if not guest_items:
            return await self.get_cart(user_id=user_id)

        user_items = await CartItem.find(CartItem.user_id == user_id).to_list()
        user_items_map = {item.product_id: item for item in user_items}

        for g_item in guest_items:
            product = await VinylProduct.find_one(VinylProduct.id == g_item.product_id)
            if g_item.product_id in user_items_map:
                u_item = user_items_map[g_item.product_id]
                new_qty = u_item.quantity + g_item.quantity
                if product:
                    new_qty = min(new_qty, product.stock_quantity)
                u_item.quantity = max(new_qty, 1)
                await u_item.save()
            else:
                qty = g_item.quantity
                if product and qty > product.stock_quantity:
                    qty = max(product.stock_quantity, 1)
                new_user_item = CartItem(
                    user_id=user_id,
                    product_id=g_item.product_id,
                    quantity=qty,
                )
                await new_user_item.insert()

            await g_item.delete()

        return await self.get_cart(user_id=user_id)
