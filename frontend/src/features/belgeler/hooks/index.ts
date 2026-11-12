"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/features/auth";
import { belgelerService } from "../services";
import type { PodAttachRequest } from "../types";

export const belgelerKeys = {
  all: ["belgeler"] as const,
  list: (capKey: string) => [...belgelerKeys.all, "list", capKey] as const,
  opsShipments: () => [...belgelerKeys.all, "ops-shipments"] as const,
};

function capKey(caps: Record<string, boolean> | null | undefined): string {
  if (!caps) return "anon";
  return Object.keys(caps)
    .filter((k) => caps[k])
    .sort()
    .join(",");
}

export function useDocumentsQuery(enabled = true) {
  const { user } = useAuth();
  const key = capKey(user?.capabilities as Record<string, boolean> | undefined);
  return useQuery({
    queryKey: belgelerKeys.list(key),
    queryFn: () => belgelerService.getDocuments(user?.capabilities),
    enabled: enabled && Boolean(user),
  });
}

/** Belgeler ekranı uyumluluk sarmalayıcısı. */
export function useDocuments() {
  const q = useDocumentsQuery();
  const snap = q.data;
  const failKeys = snap ? Object.keys(snap.errors) : [];
  const aggregateError =
    snap && snap.items.length === 0 && failKeys.length > 0
      ? Object.values(snap.errors).filter(Boolean).join(" · ")
      : null;

  return {
    documents: snap?.items ?? [],
    errors: snap?.errors ?? {},
    loading: q.isLoading,
    error: q.isError
      ? q.error instanceof Error
        ? q.error.message
        : "Belgeler alınamadı."
      : aggregateError,
    refresh: async () => {
      await q.refetch();
    },
  };
}

export function useSubmitPodDocumentMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PodAttachRequest) => belgelerService.submitPod(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: belgelerKeys.all });
    },
  });
}
