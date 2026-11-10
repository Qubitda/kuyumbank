"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

import { ApiError, apiFetch, fetchMe, logout } from "@/lib/api/client";
import type { HealthResponse, MeResponse } from "@/lib/api/types";

type LoadState =
  | { kind: "loading" }
  | { kind: "anon"; health: HealthResponse | null; healthError: string | null }
  | { kind: "auth"; me: MeResponse; health: HealthResponse | null }
  | { kind: "error"; message: string };

export function SessionPanel() {
  const router = useRouter();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      let health: HealthResponse | null = null;
      let healthError: string | null = null;
      try {
        health = await apiFetch<HealthResponse>("/health/");
      } catch (err) {
        healthError =
          err instanceof ApiError
            ? err.message
            : "API health ulaşılamadı (Django ayakta mı?).";
      }
      try {
        const me = await fetchMe();
        if (!cancelled) setState({ kind: "auth", me, health });
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          setState({ kind: "anon", health, healthError });
          return;
        }
        setState({
          kind: "error",
          message:
            err instanceof ApiError
              ? err.message
              : healthError || "Oturum durumu alınamadı.",
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function onLogout() {
    startTransition(async () => {
      try {
        await logout();
      } catch {
        /* oturum zaten düşmüş olabilir */
      }
      router.push("/login");
      router.refresh();
    });
  }

  if (state.kind === "loading") {
    return <p className="text-sm text-muted-foreground">Oturum kontrol ediliyor…</p>;
  }

  if (state.kind === "error") {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-sm text-destructive" role="alert">
          {state.message}
        </p>
        <p className="text-sm text-muted-foreground">
          Yerel: Django <code className="font-mono text-xs">runserver</code> +{" "}
          <code className="font-mono text-xs">CSRF_TRUSTED_ORIGINS=http://localhost:3000</code>
        </p>
        <Link href="/login" className="text-sm font-medium underline-offset-4 hover:underline">
          Giriş sayfası
        </Link>
      </div>
    );
  }

  if (state.kind === "anon") {
    return (
      <div className="flex flex-col gap-4">
        <HealthLine health={state.health} error={state.healthError} />
        <p className="text-sm text-muted-foreground">Oturum yok.</p>
        <Link
          href="/login"
          className="inline-flex h-10 w-fit items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
        >
          Giriş yap
        </Link>
      </div>
    );
  }

  const { me, health } = state;
  const caps = Object.entries(me.capabilities)
    .filter(([, v]) => v)
    .map(([k]) => k);

  return (
    <div className="flex flex-col gap-6">
      <HealthLine health={health} error={null} />
      <div className="flex flex-col gap-1">
        <p className="text-sm text-muted-foreground">Kullanıcı</p>
        <p className="text-base font-medium">
          {me.username}
          {me.rol ? (
            <span className="ml-2 font-mono text-xs text-muted-foreground">{me.rol}</span>
          ) : null}
        </p>
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-sm text-muted-foreground">Firma</p>
        <p className="text-base font-medium">
          {me.firma ? me.firma.ad : "—"}
          {me.firma_id != null ? (
            <span className="ml-2 font-mono text-xs text-muted-foreground">
              #{me.firma_id}
            </span>
          ) : null}
        </p>
      </div>
      <div className="flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">Capabilities (keşif)</p>
        {caps.length === 0 ? (
          <p className="text-sm">Yok</p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {caps.map((c) => (
              <li
                key={c}
                className="rounded-md border border-border px-2 py-1 font-mono text-xs"
              >
                {c}
              </li>
            ))}
          </ul>
        )}
      </div>
      <button
        type="button"
        onClick={onLogout}
        disabled={pending}
        className="h-10 w-fit rounded-md border border-border px-4 text-sm font-medium disabled:opacity-50"
      >
        {pending ? "Çıkış…" : "Çıkış yap"}
      </button>
    </div>
  );
}

function HealthLine({
  health,
  error,
}: {
  health: HealthResponse | null;
  error: string | null;
}) {
  if (error) {
    return <p className="text-sm text-destructive">Health: {error}</p>;
  }
  if (!health) {
    return <p className="text-sm text-muted-foreground">Health: —</p>;
  }
  return (
    <p className="text-sm text-muted-foreground">
      Health:{" "}
      <span className="font-mono text-foreground">
        {health.status}
        {health.api ? ` · api ${health.api}` : ""}
      </span>
    </p>
  );
}
