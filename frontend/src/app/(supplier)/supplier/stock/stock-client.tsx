"use client";

import { useEffect, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api/client";

type StockSummary = {
  results?: Array<Record<string, unknown>>;
  count?: number;
};

export function SupplierStockClient() {
  const [data, setData] = useState<StockSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<StockSummary>("/supplier/stock/")
      .then((body) => {
        if (!cancelled) {
          setData(body);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Stok alınamadı.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Stok</h1>
        <p className="text-sm text-muted-foreground">
          Özet — `/supplier/stock/`.
        </p>
      </header>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {!data && !error ? (
        <p className="text-sm text-muted-foreground">Yükleniyor…</p>
      ) : null}
      {data ? (
        <pre className="overflow-x-auto rounded-md border border-border bg-muted/40 p-3 font-mono text-xs">
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
