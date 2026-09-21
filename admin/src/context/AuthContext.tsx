import { createContext, useContext, useState, type ReactNode } from "react";
import { api, getToken, setToken } from "../api/client";

interface AuthContextValue {
  isAuthenticated: boolean;
  login: (password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(!!getToken());

  async function login(password: string) {
    const result = await api.post<{ token: string }>("/api/admin/login", { password });
    setToken(result.token);
    setIsAuthenticated(true);
  }

  function logout() {
    setToken(null);
    setIsAuthenticated(false);
  }

  return <AuthContext.Provider value={{ isAuthenticated, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
