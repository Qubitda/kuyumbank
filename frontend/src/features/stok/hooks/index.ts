"use client";

import { useEffect, useState } from "react";
import { stokService } from "../services";
import type { StockBalance } from "../types";

export function useSupplierStock() {
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    stokService
      .getSupplierStock()
      .then(setBalances)
      .catch((err) => setError(err instanceof Error ? err.message : "Stok verisi alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { balances, loading, error };
}
