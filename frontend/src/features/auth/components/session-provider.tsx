"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { ApiError, fetchMe, logout as apiLogout } from "@/lib/api/client";
import type { MeResponse } from "@/lib/api/types";
import {
  portalHomeForMe,
  resolvePortal,
  type PortalKind,
} from "@/lib/auth/portal";

type SessionState =
  | { status: "loading" }
  | { status: "anon" }
  | { status: "ready"; me: MeResponse }
  | { status: "error"; message: string };

type SessionContextValue = {
  state: SessionState;
  me: MeResponse | null;
  portal: PortalKind | null;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SessionState>({ status: "loading" });

  const refresh = useCallback(async () => {
    try {
      const me = await fetchMe();
      setState({ status: "ready", me });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setState({ status: "anon" });
        return;
      }
      setState({
        status: "error",
        message: err instanceof ApiError ? err.message : "Oturum alınamadı.",
      });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      /* ignore */
    }
    setState({ status: "anon" });
  }, []);

  const value = useMemo<SessionContextValue>(() => {
    const me = state.status === "ready" ? state.me : null;
    return {
      state,
      me,
      portal: me ? resolvePortal(me) : null,
      refresh,
      logout,
    };
  }, [state, refresh, logout]);

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession: SessionProvider gerekli");
  }
  return ctx;
}

export function useRequireSession(): {
  me: MeResponse;
  portal: PortalKind;
  home: string;
  logout: () => Promise<void>;
} {
  const { state, logout } = useSession();
  if (state.status !== "ready") {
    throw new Error("useRequireSession yalnız hazır oturumda");
  }
  const portal = resolvePortal(state.me);
  return {
    me: state.me,
    portal,
    home: portalHomeForMe(state.me),
    logout,
  };
}
