import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, clearToken, getToken, setToken } from "./api";
import type { User } from "./types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  /** username — the backend /auth/login uses "username" field, not email */
  login: (username: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => {
        clearToken();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (username, password) => {
        // POST /auth/login  { username, password }
        const res = await api.login({ username, password });
        setToken(res.access_token);
        setUser(await api.me());
      },
      register: async (_name, _email, _password) => {
        // The actual backend has no /auth/register endpoint.
        // Registration is admin-managed via backend env vars.
        // In demo mode we just set the demo token.
        const { SAMPLE_USER_USERNAME } = await import("./config");
        const res = await api.login({ username: SAMPLE_USER_USERNAME, password: _password });
        setToken(res.access_token);
        setUser(await api.me());
      },
      logout: () => {
        clearToken();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
