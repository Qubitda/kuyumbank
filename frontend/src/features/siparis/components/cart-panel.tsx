"use client";

import { useCallback, useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { newIdempotencyKey } from "@/lib/utils";

import {
  checkout,
  deleteCartLine,
  getMyCart,
  orderFromCheckout,
  patchCartLine,
} from "../services";

type Cart = components["schemas"]["BuyerCart"];
type Line = NonNullable<Cart["lines"]>[number];

export function CartPanel() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const reload = useCallback(() => {
    return getMyCart()
      .then((c) => {
        setCart(c);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Sepet alınamadı.");
      });
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  function onPatch(line: Line, miktar: string) {
    if (line.id == null) return;
    setError(null);
    startTransition(async () => {
      try {
        await patchCartLine(line.id!, { miktar }, newIdempotencyKey());
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Güncelleme başarısız.");
      }
    });
  }

  function onDelete(lineId: number) {
    setError(null);
    startTransition(async () => {
      try {
        await deleteCartLine(lineId, newIdempotencyKey());
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Silme başarısız.");
      }
    });
  }

  function onCheckout() {
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        const co = await checkout(newIdempotencyKey());
        const checkoutId =
          (co as { checkout_id?: number; id?: number }).checkout_id ??
          (co as { id?: number }).id;
        if (co.order_id) {
          setMessage(`Sipariş #${co.order_id}`);
          await reload();
          return;
        }
        if (checkoutId) {
          const order = await orderFromCheckout(
            checkoutId,
            newIdempotencyKey(),
          );
          setMessage(`Sipariş #${order.id}`);
          await reload();
          return;
        }
        setMessage("Checkout tamamlandı.");
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Checkout başarısız.");
      }
    });
  }

  const lines = cart?.lines ?? [];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Sepet</h1>
        <p className="text-sm text-muted-foreground">
          Satır sayısı:{" "}
          <span className="tabular-nums text-foreground">
            {cart?.line_count ?? lines.length}
          </span>
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

      {!cart && !error ? (
        <p className="text-sm text-muted-foreground">Yükleniyor…</p>
      ) : null}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-2 pr-3 font-medium">Satır</th>
              <th className="py-2 pr-3 font-medium">Varyant</th>
              <th className="py-2 pr-3 text-right font-medium tabular-nums">
                Miktar
              </th>
              <th className="py-2 pr-3 text-right font-medium tabular-nums">
                Birim
              </th>
              <th className="py-2 font-medium"> </th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line) =>
              line.id == null ? null : (
                <tr key={line.id} className="border-b border-border">
                  <td className="py-2 pr-3 font-mono text-xs">#{line.id}</td>
                  <td className="py-2 pr-3 tabular-nums">{line.varyant_id}</td>
                  <td className="py-2 pr-3 text-right">
                    <input
                      className="h-8 w-20 rounded-md border border-border bg-background px-2 text-right tabular-nums text-sm"
                      defaultValue={line.miktar}
                      disabled={pending}
                      onBlur={(e) => {
                        const v = e.target.value.trim();
                        if (v && v !== line.miktar) onPatch(line, v);
                      }}
                      aria-label={`Miktar satır ${line.id}`}
                    />
                  </td>
                  <td className="py-2 pr-3 text-right tabular-nums">
                    {line.birim_fiyat_vergisiz ?? "—"} {line.para_birimi || ""}
                  </td>
                  <td className="py-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={pending}
                      onClick={() => onDelete(line.id!)}
                    >
                      Sil
                    </Button>
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>

      {lines.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Sepet boş. Katalogdan sipariş veya sepete ekleme kullanın.
        </p>
      ) : (
        <Button type="button" disabled={pending} onClick={onCheckout}>
          Checkout / sipariş
        </Button>
      )}
    </div>
  );
}
