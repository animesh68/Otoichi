// API Client with automatic JWT and guest session handling
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '');

export function getAuthToken() {
  return localStorage.getItem('otoichi_token');
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('otoichi_token', token);
  } else {
    localStorage.removeItem('otoichi_token');
  }
}

export function getSessionId() {
  let sid = localStorage.getItem('otoichi_session_id');
  if (!sid) {
    sid = 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem('otoichi_session_id', sid);
  }
  return sid;
}

export async function apiRequest(endpoint, options = {}) {
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
    
    return data;
  } catch (err) {
    console.error(`Request failed for ${endpoint}:`, err);
    throw err;
  }
}
