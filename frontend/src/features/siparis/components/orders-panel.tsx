"use client";

import { useCallback, useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { newIdempotencyKey } from "@/lib/utils";

import { cancelOrder, listOrders } from "../services";

type Order = components["schemas"]["BuyerOrder"];

export function OrdersPanel() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const reload = useCallback(() => {
    return listOrders()
      .then((page) => {
        setOrders(page.results ?? []);
        setError(null);
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Sipariş listesi alınamadı.",
        );
      });
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  function onCancel(id: number) {
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        await cancelOrder(id, newIdempotencyKey());
        setMessage(`Sipariş #${id} iptal edildi`);
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "İptal başarısız.");
      }
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Siparişler</h1>
        <p className="text-sm text-muted-foreground">
          Alıcı siparişleri — tedarikçi kimliği yok.
        </p>
      </header>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="text-sm text-foreground" role="status">
          {message}
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
              <th className="py-2 pr-3 font-medium">Tarih</th>
              <th className="py-2 font-medium"> </th>
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
                <td className="py-2 pr-3 text-muted-foreground">
                  {o.olusturma_tarihi
                    ? new Date(o.olusturma_tarihi).toLocaleString("tr-TR")
                    : "—"}
                </td>
                <td className="py-2">
                  {o.allowed_actions?.includes("cancel") ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={pending}
                      onClick={() => onCancel(o.id)}
                    >
                      İptal
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {orders.length === 0 && !error ? (
        <p className="text-sm text-muted-foreground">Sipariş yok.</p>
      ) : null}
    </div>
  );
}
