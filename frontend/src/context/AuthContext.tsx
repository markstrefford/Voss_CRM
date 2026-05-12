import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { getMe } from '@/api';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, remember?: boolean) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('token') || sessionStorage.getItem('token')
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      getMe()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('token');
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const loginFn = (newToken: string, remember = false) => {
    if (remember) {
      localStorage.setItem('rememberMe', 'true');
      localStorage.setItem('token', newToken);
      sessionStorage.removeItem('token');
    } else {
      localStorage.removeItem('rememberMe');
      localStorage.removeItem('token');
      sessionStorage.setItem('token', newToken);
    }
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('rememberMe');
    sessionStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login: loginFn, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
