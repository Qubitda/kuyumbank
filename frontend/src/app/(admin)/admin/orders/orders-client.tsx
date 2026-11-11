"use client";

import { useEffect, useState } from "react";

import { listOrders } from "@/features/siparis/services";
import { ApiError, apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type Order = components["schemas"]["BuyerOrder"];

type OpsSummary = {
  total: number;
  by_durum: Record<string, number>;
};

export function AdminOrdersClient() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [summary, setSummary] = useState<OpsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      listOrders(),
      apiFetch<OpsSummary>("/ops/orders/summary/").catch(() => null),
    ])
      .then(([page, sum]) => {
        if (cancelled) return;
        setOrders(page.results ?? []);
        setSummary(sum);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Sipariş listesi alınamadı.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Siparişler</h1>
        <p className="text-sm text-muted-foreground">
          Siparişler admin yüzeyine düşer; tedarikçiye atama RFQ eşleştirme ile.
        </p>
      </header>
      {summary ? (
        <p className="text-sm text-muted-foreground">
          Toplam{" "}
          <span className="tabular-nums text-foreground">{summary.total}</span>
          {" · "}
          {Object.entries(summary.by_durum)
            .map(([k, v]) => `${k}: ${v}`)
            .join(" · ")}
        </p>
      ) : null}
      {loading ? (
        <p className="text-sm text-muted-foreground">Yükleniyor…</p>
      ) : null}
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[32rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-2 pr-3 font-medium">ID</th>
              <th className="py-2 pr-3 font-medium">Durum</th>
              <th className="py-2 pr-3 text-right font-medium tabular-nums">
                Satır
              </th>
              <th className="py-2 font-medium">Oluşturma</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} className="border-b border-border">
                <td className="py-2 pr-3 font-mono text-xs">#{o.id}</td>
                <td className="py-2 pr-3">{o.durum}</td>
                <td className="py-2 pr-3 text-right tabular-nums">
                  {o.line_count ?? o.lines?.length ?? "—"}
                </td>
                <td className="py-2 text-muted-foreground">
                  {o.olusturma_tarihi
                    ? new Date(o.olusturma_tarihi).toLocaleString("tr-TR")
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!loading && !error && orders.length === 0 ? (
        <p className="text-sm text-muted-foreground">Sipariş yok.</p>
      ) : null}
    </div>
  );
}
