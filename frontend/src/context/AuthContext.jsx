import React, { createContext, useContext, useState, useEffect } from 'react';
import { AuthService } from '../api/services';
import { setAuthToken, getAuthToken } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const data = await AuthService.getMe();
      setUser(data);
    } catch (err) {
      console.warn('Auth check failed:', err);
      setAuthToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (email, password) => {
    const data = await AuthService.login(email, password);
    if (data?.access_token) {
      setAuthToken(data.access_token);
      await fetchCurrentUser();
    }
    return data;
  };

  const register = async (userData) => {
    const data = await AuthService.register(userData);
    if (data?.access_token) {
      setAuthToken(data.access_token);
      await fetchCurrentUser();
    }
    return data;
  };

  const logout = () => {
    setAuthToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
