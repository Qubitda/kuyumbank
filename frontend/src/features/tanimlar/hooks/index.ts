"use client";

import { useQuery } from "@tanstack/react-query";
import { tanimlarService } from "../services";

export const tanimlarKeys = {
  all: ["tanimlar"] as const,
  salesChannels: () => [...tanimlarKeys.all, "sales-channels"] as const,
};

export function useSalesChannelsQuery(enabled = true) {
  return useQuery({
    queryKey: tanimlarKeys.salesChannels(),
    queryFn: () => tanimlarService.getSalesChannelsPage(),
    enabled,
  });
}

/** Tanımlar ekranı uyumluluk sarmalayıcısı. */
export function useSalesChannels() {
  const q = useSalesChannelsQuery();
  return {
    page: q.data ?? null,
    channels: q.data?.results ?? [],
    loading: q.isLoading,
    error: q.isError
      ? q.error instanceof Error
        ? q.error.message
        : "Tanım verileri alınamadı."
      : null,
    refresh: () => void q.refetch(),
  };
}
