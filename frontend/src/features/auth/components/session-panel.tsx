"use client";

import React, { useEffect, useState, useTransition } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiFetch, fetchMe, logout, ApiError } from "@/lib/api/client";
import type { HealthResponse, MeResponse } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShieldCheck, UserCheck, Activity, LogOut } from "lucide-react";

type LoadState =
  | { kind: "loading" }
  | { kind: "anon"; health: HealthResponse | null; healthError: string | null }
  | { kind: "auth"; me: MeResponse; health: HealthResponse | null }
  | { kind: "error"; message: string };

export function SessionPanel() {
  const navigate = useNavigate();
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
            : "Backend health servisine ulaşılamadı.";
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

  const handleLogout = () => {
    startTransition(async () => {
      try {
        await logout();
      } catch {
        // Oturum zaten düşmüş olabilir
      }
      navigate("/login");
    });
  };

  if (state.kind === "loading") {
    return (
      <div className="rounded-[8px] border border-border bg-card p-6">
        <p className="text-sm text-muted-foreground animate-pulse">
          Oturum ve yetki durumu kontrol ediliyor…
        </p>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="flex flex-col gap-3 rounded-[8px] border border-border bg-card p-6">
        <p className="text-sm text-destructive" role="alert">
          {state.message}
        </p>
        <p className="text-xs text-muted-foreground">
          Backend: Django <code className="font-mono">runserver</code> aynı-origin rewrite (/api/v1) üzerinden beklenmektedir.
        </p>
        <div className="pt-2">
          <Button asChild variant="outline" size="sm">
            <Link to="/login">Giriş Sayfası</Link>
          </Button>
        </div>
      </div>
    );
  }

  if (state.kind === "anon") {
    return (
      <div className="flex flex-col gap-4 rounded-[8px] border border-border bg-card p-6">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              API Health:{" "}
              <span className="font-mono text-foreground font-medium">
                {state.health?.status || "bağlantı bekleniyor"}
              </span>
            </span>
          </div>
          <Badge variant="outline">Aktif Oturum Yok</Badge>
        </div>

        <p className="text-sm text-muted-foreground">
          Şu anda doğrulanmış bir session cookie bulunmuyor. Domain yetkilerini görüntülemek için oturum açabilirsiniz.
        </p>

        <div>
          <Button asChild size="default">
            <Link to="/login">Oturum Aç</Link>
          </Button>
        </div>
      </div>
    );
  }

  const { me, health } = state;
  const activeCapabilities = Object.entries(me.capabilities)
    .filter(([, active]) => active)
    .map(([key]) => key);

  return (
    <div className="flex flex-col gap-6 rounded-[8px] border border-border bg-card p-6">
      {/* Üst Bilgi Satırı */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div className="flex items-center gap-2 text-foreground font-semibold text-base">
          <UserCheck className="h-5 w-5 text-foreground" />
          <span>{me.username}</span>
          {me.rol && (
            <Badge variant="secondary" className="font-mono text-[11px]">
              {me.rol}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            API Health:{" "}
            <span className="font-mono text-foreground">
              {health?.status || "200 OK"}
            </span>
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleLogout}
            disabled={pending}
            className="text-xs gap-1.5"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>{pending ? "Çıkılıyor…" : "Çıkış Yap"}</span>
          </Button>
        </div>
      </div>

      {/* Kimlik & Firma Bilgileri */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <span className="text-muted-foreground font-medium">Bağlı Firma</span>
          <p className="text-sm font-medium text-foreground">
            {me.firma?.ad || "— (Platform Konsolu)"}
            {me.firma_id != null && (
              <span className="ml-2 font-mono text-xs text-muted-foreground">
                [ID: {me.firma_id}]
              </span>
            )}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-muted-foreground font-medium">Tenant İzolasyonu</span>
          <p className="text-xs text-muted-foreground">
            {me.firma?.platform_mu
              ? "Platform yöneticisi — tüm operasyonel denetim açık."
              : me.firma?.alici_mi
              ? "Alıcı yetki profili — kör havuz aktif."
              : me.firma?.tedarikci_mi
              ? "Tedarikçi yetki profili — anonim teklif alanı."
              : "Özel rol"}
          </p>
        </div>
      </div>

      {/* Aktif Yetkiler (Capabilities Keşfi) */}
      <div className="space-y-2 border-t border-border pt-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-medium text-foreground">
            Doğrulanmış Yetkiler (Capabilities /me)
          </span>
        </div>

        {activeCapabilities.length === 0 ? (
          <p className="text-xs text-muted-foreground">Tanımlı özel yetki bulunamadı.</p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {activeCapabilities.map((cap) => (
              <span
                key={cap}
                className="inline-flex rounded-[4px] border border-border bg-muted/60 px-2 py-0.5 font-mono text-[11px] text-foreground"
              >
                {cap}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
