"use client";

import { useEffect, useState } from "react";
import { tanimlarService } from "../services";
import type { SalesChannel } from "../types";

export function useSalesChannels() {
  const [channels, setChannels] = useState<SalesChannel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    tanimlarService
      .getSalesChannels()
      .then(setChannels)
      .catch((err) => setError(err instanceof Error ? err.message : "Veri alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { channels, loading, error };
}
