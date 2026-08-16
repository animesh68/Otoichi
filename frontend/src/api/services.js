import { apiRequest } from './client';

export const CatalogService = {
  getProducts: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.append('q', params.search);
    if (params.genre) query.append('genre', params.genre);
    if (params.artist_id) query.append('artist_id', params.artist_id);
    if (params.album_id) query.append('album_id', params.album_id);
    if (params.format) query.append('format', params.format);
    if (params.condition) query.append('condition', params.condition);
    if (params.product_type) query.append('product_type', params.product_type);
    if (params.min_price) query.append('min_price', params.min_price);
    if (params.max_price) query.append('max_price', params.max_price);
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('page_size', params.limit);
    
    const qs = query.toString();
    return apiRequest(`/products/${qs ? '?' + qs : ''}`);
  },

  getProductById: async (id) => {
    return apiRequest(`/products/${id}`);
  },

  getAlbums: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.genre) query.append('genre', params.genre);
    if (params.search) query.append('q', params.search);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('page_size', params.limit || 50);
    const qs = query.toString();
    return apiRequest(`/albums/${qs ? '?' + qs : ''}`);
  },

  getAlbumById: async (id) => {
    return apiRequest(`/albums/${id}`);
  },

  getArtists: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.append('q', params.search);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('page_size', params.limit || 50);
    const qs = query.toString();
    return apiRequest(`/artists/${qs ? '?' + qs : ''}`);
  },

  getArtistById: async (id) => {
    return apiRequest(`/artists/${id}`);
  }
};

export const CartService = {
  getCart: async () => {
    return apiRequest('/cart/');
  },

  addItem: async (productId, quantity = 1) => {
    return apiRequest('/cart/items', {
      method: 'POST',
      body: JSON.stringify({
        product_id: productId,
        quantity: quantity
      })
    });
  },

  updateItem: async (cartItemId, quantity) => {
    return apiRequest(`/cart/items/${cartItemId}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity })
    });
  },

  removeItem: async (cartItemId) => {
    return apiRequest(`/cart/items/${cartItemId}`, {
      method: 'DELETE'
    });
  },

  clearCart: async () => {
    return apiRequest('/cart/clear', {
      method: 'DELETE'
    });
  }
};

export const CheckoutService = {
  validateCoupon: async (code, subtotal = 50.0) => {
    return apiRequest('/coupons/validate', {
      method: 'POST',
      body: JSON.stringify({
        code: code,
        subtotal: subtotal
      })
    });
  },

  getSummary: async (payload = {}) => {
    return apiRequest('/checkout/summary', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  createIntent: async (payload = {}) => {
    return apiRequest('/checkout/create-intent', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  createZeroTotalOrder: async (payload = {}) => {
    return apiRequest('/checkout/zero-total-order', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  completeCheckout: async (payload = {}) => {
    return apiRequest('/checkout/complete', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
};

export const OrderService = {
  getOrders: async () => {
    return apiRequest('/orders/');
  },

  getOrderById: async (id) => {
    return apiRequest(`/orders/${id}`);
  }
};

export const AuthService = {
  login: async (email, password) => {
    return apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  register: async (userData) => {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  getMe: async () => {
    return apiRequest('/auth/me');
  }
};
