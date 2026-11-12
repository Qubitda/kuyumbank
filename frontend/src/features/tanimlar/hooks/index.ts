"use client";

import { useCallback, useEffect, useState } from "react";
import { tanimlarService } from "../services";
import type { SalesChannel, SalesChannelPage } from "../types";

export function useSalesChannels() {
  const [page, setPage] = useState<SalesChannelPage | null>(null);
  const [channels, setChannels] = useState<SalesChannel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await tanimlarService.getSalesChannelsPage();
      setPage(data);
      setChannels(data.results);
    } catch (err) {
      setPage(null);
      setChannels([]);
      setError(err instanceof Error ? err.message : "Tanım verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { page, channels, loading, error, refresh };
}
