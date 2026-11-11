"use client";

import { useEffect, useState } from "react";
import { fiyatlamaService } from "../services";
import type { PriceQuote } from "../types";

export function useQuotes() {
  const [quotes, setQuotes] = useState<PriceQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fiyatlamaService
      .getQuotes()
      .then(setQuotes)
      .catch((err) => setError(err instanceof Error ? err.message : "Fiyat teklifleri alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { quotes, loading, error };
}
