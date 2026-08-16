import React, { createContext, useContext, useState, useEffect } from 'react';
import { CartService } from '../api/services';

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [cart, setCart] = useState({ items: [], subtotal: 0, total: 0 });
  const [itemCount, setItemCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [coupon, setCoupon] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchCart = async () => {
    try {
      setLoading(true);
      const data = await CartService.getCart();
      if (data) {
        setCart(data);
        const count = (data.items || []).reduce((acc, it) => acc + it.quantity, 0);
        setItemCount(count);
      }
    } catch (err) {
      console.warn('Could not fetch cart:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const addToCart = async (product, quantity = 1) => {
    try {
      const pId = product.id || product.product_id;
      const res = await CartService.addItem(pId, quantity);
      await fetchCart();
      const name = product.title || product.album_title || 'Record';
      showToast(`Added "${name}" to cart`);
      return res;
    } catch (err) {
      showToast(err.message || 'Failed to add item to cart');
      throw err;
    }
  };

  const updateQuantity = async (cartItemId, quantity) => {
    try {
      if (quantity <= 0) {
        await CartService.removeItem(cartItemId);
      } else {
        await CartService.updateItem(cartItemId, quantity);
      }
      await fetchCart();
    } catch (err) {
      showToast(err.message || 'Failed to update item quantity');
    }
  };

  const removeFromCart = async (cartItemId) => {
    try {
      await CartService.removeItem(cartItemId);
      await fetchCart();
      showToast('Item removed from cart');
    } catch (err) {
      showToast(err.message || 'Failed to remove item');
    }
  };

  const clearCart = async () => {
    try {
      await CartService.clearCart();
      setCart({ items: [], subtotal: 0, total: 0 });
      setItemCount(0);
      setCoupon(null);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <CartContext.Provider value={{
      cart,
      itemCount,
      loading,
      coupon,
      setCoupon,
      addToCart,
      updateQuantity,
      removeFromCart,
      clearCart,
      fetchCart,
      toastMessage
    }}>
      {children}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: '32px',
          right: '32px',
          background: 'var(--taupe)',
          border: '1px solid var(--brass)',
          color: 'var(--ink)',
          padding: '12px 20px',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
          zIndex: 9999,
          fontFamily: 'var(--font-body)',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          animation: 'fadeIn 0.2s ease-out'
        }}>
          <span style={{ color: 'var(--brass)' }}>●</span>
          {toastMessage}
        </div>
      )}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
