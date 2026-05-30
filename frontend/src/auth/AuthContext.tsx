import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { api } from "../api/client";
import type { Role, TokenResponse, User } from "../api/types";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
}

interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
  department?: string;
  role: Role;
}

const AuthCtx = createContext<AuthState | undefined>(undefined);

const TOKEN_KEY = "failsafe_token";
const USER_KEY = "failsafe_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY)
  );
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  });
  const [loading, setLoading] = useState(false);

  const persist = useCallback((data: TokenResponse) => {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const { data } = await api.post<TokenResponse>("/auth/login", {
          email,
          password,
        });
        persist(data);
      } finally {
        setLoading(false);
      }
    },
    [persist]
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      setLoading(true);
      try {
        const { data } = await api.post<TokenResponse>("/auth/register", input);
        persist(data);
      } finally {
        setLoading(false);
      }
    },
    [persist]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    if (!token) return;
    api
      .get<User>("/auth/me")
      .then(({ data }) => {
        setUser(data);
        localStorage.setItem(USER_KEY, JSON.stringify(data));
      })
      .catch(() => logout());
  }, [token, logout]);

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout }),
    [user, token, loading, login, register, logout]
  );

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
