"use client";

import { useAuthContext } from "../components/auth-provider";

/** AuthProvider üzerinden oturum durumu. */
export function useAuth() {
  const ctx = useAuthContext();
  return {
    user: ctx.user,
    loading: ctx.loading,
    error: ctx.error,
    mfaPending: ctx.mfaPending,
    isAuthenticated: ctx.isAuthenticated,
    refresh: ctx.refresh,
    logout: ctx.logout,
    setSessionUser: ctx.setSessionUser,
  };
}
