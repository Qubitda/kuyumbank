"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, Layers } from "lucide-react";

export function DomainLoading({ label }: { label: string }) {
  return (
    <div
      className="flex h-48 w-full items-center justify-center"
      aria-live="polite"
      role="status"
    >
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
        <span>{label} verileri yükleniyor…</span>
      </div>
    </div>
  );
}

export function DomainError({
  label,
  error,
  reset,
}: {
  label: string;
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(`[${label} Segment Hatası]:`, error);
  }, [label, error]);

  return (
    <div
      className="flex flex-col gap-4 rounded-[8px] border border-border bg-card p-6"
      role="alert"
    >
      <div className="flex items-center gap-2 text-destructive">
        <AlertCircle className="h-5 w-5" />
        <h2 className="text-base font-semibold">{label} segmenti yüklenemedi</h2>
      </div>

      <p className="text-sm text-muted-foreground">
        {error.message || "Bilinmeyen bir hata meydana geldi."}
      </p>

      <div className="flex items-center gap-3 pt-2">
        <Button variant="outline" size="sm" onClick={reset}>
          Yeniden Dene
        </Button>
        <Button asChild variant="ghost" size="sm">
          <Link href="/">Genel Bakışa Dön</Link>
        </Button>
      </div>
    </div>
  );
}

export interface DomainPlaceholderProps {
  title: string;
  backendApp: string;
  description?: string;
  note?: string;
}

export function DomainPlaceholder({
  title,
  backendApp,
  description,
  note,
}: DomainPlaceholderProps) {
  return (
    <div className="flex flex-col gap-6">
      {/* Sayfa Başlığı ve İkincil Bilgi */}
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          <span className="inline-flex items-center rounded-[4px] border border-border bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">
            backend: {backendApp}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          {description ||
            `Django "${backendApp}" domain app ile birebir paralel Next.js modülü.`}
        </p>
      </div>

      {/* Domain Durum Kartı */}
      <div className="rounded-[8px] border border-border bg-card p-6 space-y-4">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Layers className="h-4 w-4 text-muted-foreground" />
          <span>Domain İskeleti Hazır</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1">
            <p className="font-medium text-foreground">Mimari Eşleme</p>
            <p className="text-muted-foreground font-mono">
              src/features/{backendApp}/
            </p>
            <p className="text-muted-foreground">
              components · types · services · hooks · schemas
            </p>
          </div>

          <div className="space-y-1">
            <p className="font-medium text-foreground">Kör Havuz & Güvenlik</p>
            <p className="text-muted-foreground">
              Alıcı ekranında tedarikçi kimliği ve gizli maliyet gösterilmez.
              Yazma işlemlerinde yetki backend otoritesindedir.
            </p>
          </div>
        </div>

        {note && (
          <div className="rounded-[6px] bg-muted/60 p-3 text-xs text-muted-foreground border-l-2 border-primary">
            {note}
          </div>
        )}
      </div>
    </div>
  );
}
