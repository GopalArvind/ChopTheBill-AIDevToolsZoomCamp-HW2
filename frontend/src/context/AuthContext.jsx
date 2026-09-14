import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../services/api.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProfile().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  const signup = async (payload) => {
    const data = await api.signup(payload);
    setUser(data.user);
    return data;
  };
  const login = async (payload) => {
    const data = await api.login(payload);
    setUser(data.user);
    return data;
  };
  const logout = async () => {
    await api.logout();
    localStorage.removeItem('chopthebil_token');
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, loading, signup, login, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
