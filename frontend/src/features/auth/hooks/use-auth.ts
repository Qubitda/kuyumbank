"use client";

import { useEffect, useState, useTransition } from "react";
import { authService } from "../services/auth-service";
import type { MeResponse } from "../types/auth";
import { ApiError } from "@/lib/api/client";

export function useAuth() {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const refresh = () => {
    setLoading(true);
    authService
      .getMe()
      .then((data) => {
        setUser(data);
        setError(null);
      })
      .catch((err) => {
        setUser(null);
        if (err instanceof ApiError && err.status === 401) {
          setError(null);
        } else {
          setError(err instanceof Error ? err.message : "Oturum alınamadı.");
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    refresh();
  }, []);

  const logout = () => {
    startTransition(async () => {
      try {
        await authService.logout();
      } catch {
        // Oturum düşmüş olabilir
      }
      setUser(null);
    });
  };

  return {
    user,
    loading: loading || isPending,
    error,
    isAuthenticated: Boolean(user),
    refresh,
    logout,
  };
}
