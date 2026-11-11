"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

import { listCatalog } from "../services";

type Item = components["schemas"]["BuyerCatalogItem"];

export function CatalogList() {
  const [items, setItems] = useState<Item[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listCatalog({ search: q || undefined })
      .then((page) => {
        if (!cancelled) {
          setItems(page.results ?? []);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Katalog alınamadı.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [q]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="catalog-search" className="text-sm text-muted-foreground">
          Ara
        </label>
        <input
          id="catalog-search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="h-10 rounded-md border border-border bg-background px-3 text-sm"
          placeholder="Ürün adı veya kod"
        />
      </div>
      {loading ? (
        <p className="text-sm text-muted-foreground">Yükleniyor…</p>
      ) : null}
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <p className="text-sm text-muted-foreground">Kayıt yok.</p>
      ) : null}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-2 pr-3 font-medium">Ad</th>
              <th className="py-2 pr-3 font-medium">Kod</th>
              <th className="py-2 pr-3 font-medium">Kategori</th>
              <th className="py-2 pr-3 font-medium">Ayar</th>
              <th className="py-2 pr-3 text-right font-medium tabular-nums">
                Varyant
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b border-border">
                <td className="py-2 pr-3">
                  <Link
                    href={`/buyer/catalog/${item.id}`}
                    className="font-medium underline-offset-4 hover:underline"
                  >
                    {item.ad}
                  </Link>
                </td>
                <td className="py-2 pr-3 font-mono text-xs text-muted-foreground">
                  {item.platform_kodu || "—"}
                </td>
                <td className="py-2 pr-3">{item.kategori || "—"}</td>
                <td className="py-2 pr-3">{item.ayar || "—"}</td>
                <td className="py-2 text-right tabular-nums">
                  {item.varyant_count ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
