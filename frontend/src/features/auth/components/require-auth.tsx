"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import type { Capabilities } from "@/lib/api/types";
import {
  portalHome,
  resolvePortal,
  type PortalKind,
} from "@/lib/auth/portal";

import { useSession } from "./session-provider";

type Props = {
  children: React.ReactNode;
  /** Bu portal dışı kullanıcıyı kendi köküne gönder. */
  portal?: PortalKind;
  /** En az bir capability true olmalı (UI gizleme; güvenlik değil). */
  anyOf?: (keyof Capabilities)[];
};

export function RequireAuth({ children, portal, anyOf }: Props) {
  const { state } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (state.status === "anon") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (state.status === "ready" && portal) {
      const actual = resolvePortal(state.me);
      if (actual !== portal) {
        router.replace(portalHome(actual));
      }
    }
  }, [state, portal, router, pathname]);

  if (state.status === "loading") {
    return (
      <p className="text-sm text-muted-foreground">Oturum kontrol ediliyor…</p>
    );
  }

  if (state.status === "error") {
    return (
      <div className="flex flex-col gap-2">
        <p className="text-sm text-destructive" role="alert">
          {state.message}
        </p>
        <Link href="/login" className="text-sm underline-offset-4 hover:underline">
          Giriş
        </Link>
      </div>
    );
  }

  if (state.status === "anon") {
    return (
      <p className="text-sm text-muted-foreground">Giriş sayfasına yönlendiriliyor…</p>
    );
  }

  if (portal && resolvePortal(state.me) !== portal) {
    return (
      <p className="text-sm text-muted-foreground">Doğru portala yönlendiriliyor…</p>
    );
  }

  if (anyOf && anyOf.length > 0) {
    const ok = anyOf.some((k) => state.me.capabilities[k] === true);
    if (!ok) {
      return (
        <p className="text-sm text-destructive" role="alert">
          Bu sayfa için yetkiniz yok.
        </p>
      );
    }
  }

  return <>{children}</>;
}
