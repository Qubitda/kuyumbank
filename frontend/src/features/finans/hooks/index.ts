"use client";

import { useEffect, useState } from "react";
import { finansService } from "../services";
import type { CariHesap } from "../types";

export function useFinance() {
  const [cari, setCari] = useState<CariHesap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    finansService
      .getMyFinance()
      .then(setCari)
      .catch((err) => setError(err instanceof Error ? err.message : "Finans bilgisi alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { cari, loading, error };
}
