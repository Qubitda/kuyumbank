"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { ShoppingCart, Package, Building, Hash } from "lucide-react";

interface MeDashboard {
  cart_id: number;
  cart_line_count: number;
  firma_ad: string;
  firma_id: number | null;
  firma_kodu: string;
  order_count: number;
}

export function DashboardCounters() {
  const [data, setData] = useState<MeDashboard | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<MeDashboard>("/me/dashboard/")
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch(() => {
        // Oturum yoksa veya 401 ise sessizce geçer
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (!data) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div className="rounded-[8px] border border-border bg-card p-4 space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Building className="h-3.5 w-3.5" />
          <span>Firma</span>
        </div>
        <p className="text-base font-semibold text-foreground truncate">
          {data.firma_ad || "—"}
        </p>
      </div>

      <div className="rounded-[8px] border border-border bg-card p-4 space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Hash className="h-3.5 w-3.5" />
          <span>Firma Kodu</span>
        </div>
        <p className="text-base font-semibold font-mono text-foreground">
          {data.firma_kodu || "—"}
        </p>
      </div>

      <Link
        href="/siparis"
        className="rounded-[8px] border border-border bg-card p-4 space-y-1 hover:bg-muted/40 transition-colors"
      >
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <ShoppingCart className="h-3.5 w-3.5" />
          <span>Sepetteki Kalem</span>
        </div>
        <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
          {data.cart_line_count}
        </p>
      </Link>

      <Link
        href="/siparis"
        className="rounded-[8px] border border-border bg-card p-4 space-y-1 hover:bg-muted/40 transition-colors"
      >
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Package className="h-3.5 w-3.5" />
          <span>Toplam Sipariş</span>
        </div>
        <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
          {data.order_count}
        </p>
      </Link>
    </div>
  );
}
