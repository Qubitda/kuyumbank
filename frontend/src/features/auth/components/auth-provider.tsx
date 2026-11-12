"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "@/lib/api/client";
import type { MeResponse } from "@/lib/api/types";
import { authService } from "../services/auth-service";
import { DomainLoading } from "@/components/route-states";

interface AuthContextValue {
  user: MeResponse | null;
  loading: boolean;
  error: string | null;
  mfaPending: boolean;
  isAuthenticated: boolean;
  refresh: () => Promise<MeResponse | null>;
  setSessionUser: (user: MeResponse | null, opts?: { mfaPending?: boolean }) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const PUBLIC_PATHS = new Set(["/login"]);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mfaPending, setMfaPending] = useState(false);

  const setSessionUser = useCallback(
    (next: MeResponse | null, opts?: { mfaPending?: boolean }) => {
      setUser(next);
      setMfaPending(Boolean(opts?.mfaPending));
      setError(null);
    },
    []
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const me = await authService.getMe();
      setUser(me);
      setMfaPending(false);
      setError(null);
      return me;
    } catch (err) {
      setUser(null);
      if (err instanceof ApiError && err.problem.code === "mfa_required") {
        setMfaPending(true);
        setError(null);
        return null;
      }
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        setMfaPending(false);
        setError(null);
        return null;
      }
      setMfaPending(false);
      setError(err instanceof Error ? err.message : "Oturum alınamadı.");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch {
      // oturum zaten düşmüş olabilir
    }
    setUser(null);
    setMfaPending(false);
    setError(null);
    navigate("/login", { replace: true });
  }, [navigate]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const onExpired = (event: Event) => {
      const detail = (event as CustomEvent).detail as
        | { code?: string; status?: number }
        | undefined;
      if (detail?.code === "mfa_required") {
        setUser(null);
        setMfaPending(true);
        if (!PUBLIC_PATHS.has(pathname)) {
          navigate("/login", { replace: true });
        }
        return;
      }
      setUser(null);
      setMfaPending(false);
      if (!PUBLIC_PATHS.has(pathname)) {
        navigate("/login", { replace: true });
      }
    };
    window.addEventListener("kuyumbank:auth-expired", onExpired);
    return () => window.removeEventListener("kuyumbank:auth-expired", onExpired);
  }, [pathname, navigate]);

  useEffect(() => {
    if (loading) return;
    const isPublic = PUBLIC_PATHS.has(pathname);

    if ((!user || mfaPending) && !isPublic) {
      navigate("/login", { replace: true });
      return;
    }

    if (user && !mfaPending && isPublic) {
      navigate("/", { replace: true });
    }
  }, [loading, user, mfaPending, pathname, navigate]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      error,
      mfaPending,
      isAuthenticated: Boolean(user) && !mfaPending,
      refresh,
      setSessionUser,
      logout,
    }),
    [user, loading, error, mfaPending, refresh, setSessionUser, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuthContext AuthProvider içinde kullanılmalıdır.");
  }
  return ctx;
}

/** Korumalı portal yüzeyi — oturum yoksa login’e yönlendirir. */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { loading, isAuthenticated } = useAuthContext();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <DomainLoading label="Oturum" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <DomainLoading label="Giriş yönlendirmesi" />
      </div>
    );
  }

  return <>{children}</>;
}
