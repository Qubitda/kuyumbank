"use client";

import { useEffect, useState } from "react";
import { urunlerService } from "../services";
import type { BuyerCatalogItem, BuyerCatalogPage } from "../types";

export function useCatalog(filters?: Record<string, string>) {
  const [products, setProducts] = useState<BuyerCatalogItem[]>([]);
  const [page, setPage] = useState<BuyerCatalogPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    urunlerService
      .getCatalog(filters)
      .then((data) => {
        if (cancelled) return;
        setPage(data);
        setProducts(data?.results || []);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Katalog alınamadı");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [filters]);

  return { products, page, loading, error };
}
