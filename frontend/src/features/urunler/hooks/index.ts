"use client";

import { useEffect, useState } from "react";
import { urunlerService } from "../services";
import type { BuyerCatalogItem } from "../types";

export function useCatalog(filters?: Record<string, string>) {
  const [products, setProducts] = useState<BuyerCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    urunlerService
      .getCatalog(filters)
      .then((data) => setProducts(data?.results || []))
      .catch((err) => setError(err instanceof Error ? err.message : "Katalog alınamadı"))
      .finally(() => setLoading(false));
  }, [filters]);

  return { products, loading, error };
}
