// API Client with automatic JWT, guest session handling, in-flight deduplication, and SWR memory caching
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '');

// In-flight promise deduplication map
const inFlightRequests = new Map();

// In-memory SWR client cache with TTL
const clientCache = new Map();
const CLIENT_CACHE_TTL_MS = 45 * 1000; // 45 seconds

export function getAuthToken() {
  return localStorage.getItem('otoichi_token');
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('otoichi_token', token);
  } else {
    localStorage.removeItem('otoichi_token');
  }
  // Clear client cache on auth changes
  clientCache.clear();
}

export function getSessionId() {
  let sid = localStorage.getItem('otoichi_session_id');
  if (!sid) {
    sid = 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem('otoichi_session_id', sid);
  }
  return sid;
}

export function clearClientCache() {
  clientCache.clear();
}

function isCacheable(endpoint, method) {
  if (method && method.toUpperCase() !== 'GET') return false;
  // Never cache user-scoped or checkout endpoints
  if (
    endpoint.includes('/cart') ||
    endpoint.includes('/checkout') ||
    endpoint.includes('/orders') ||
    endpoint.includes('/auth/me') ||
    endpoint.includes('/admin')
  ) {
    return false;
  }
  return true;
}

export async function apiRequest(endpoint, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const token = getAuthToken();
  const sessionId = getSessionId();

  const headers = {
    'Content-Type': 'application/json',
    'X-Session-ID': sessionId,
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  const config = {
    ...options,
    headers
  };

  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE}${normalizedEndpoint}`;
  const cacheKey = `${method}:${fullUrl}`;

  // 1. Check in-memory cache for cacheable GET requests
  if (isCacheable(normalizedEndpoint, method)) {
    const cachedEntry = clientCache.get(cacheKey);
    if (cachedEntry && Date.now() - cachedEntry.timestamp < CLIENT_CACHE_TTL_MS) {
      return cachedEntry.data;
    }
  }

  // 2. In-flight request deduplication for concurrent GETs
  if (method === 'GET' && inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey);
  }

  // 3. Clear cache on mutations
  if (method !== 'GET') {
    clientCache.clear();
  }

  const fetchPromise = (async () => {
    try {
      const res = await fetch(fullUrl, config);

      if (res.status === 204) {
        return null;
      }

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        const errorMsg = data?.detail || `API error: ${res.status} ${res.statusText}`;
        const err = new Error(errorMsg);
        err.status = res.status;
        err.data = data;
        throw err;
      }

      // Save to client cache if eligible
      if (isCacheable(normalizedEndpoint, method)) {
        clientCache.set(cacheKey, { data, timestamp: Date.now() });
      }

      return data;
    } finally {
      inFlightRequests.delete(cacheKey);
    }
  })();

  if (method === 'GET') {
    inFlightRequests.set(cacheKey, fetchPromise);
  }

  return fetchPromise;
}
