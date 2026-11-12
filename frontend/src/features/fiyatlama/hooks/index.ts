"use client";

import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fiyatlamaService } from "../services";
import type { PriceLock, PriceQuote } from "../types";

const QUOTE_KEY = "kuyumbank.session.quote_ids";
const LOCK_KEY = "kuyumbank.session.lock_ids";

function readIds(key: string): number[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as number[];
    return Array.isArray(parsed) ? parsed.filter((n) => Number.isFinite(n)) : [];
  } catch {
    return [];
  }
}

function writeIds(key: string, ids: number[]) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(key, JSON.stringify([...new Set(ids)]));
}

export function rememberQuoteId(id: number) {
  writeIds(QUOTE_KEY, [...readIds(QUOTE_KEY), id]);
}

export function rememberLockId(id: number) {
  writeIds(LOCK_KEY, [...readIds(LOCK_KEY), id]);
}

export const fiyatlamaKeys = {
  all: ["fiyatlama"] as const,
  session: (extraQuoteIds: number[] = []) =>
    [...fiyatlamaKeys.all, "session", [...extraQuoteIds].sort((a, b) => a - b)] as const,
  quote: (id: number | string) =>
    [...fiyatlamaKeys.all, "quote", String(id)] as const,
  lock: (id: number | string) =>
    [...fiyatlamaKeys.all, "lock", String(id)] as const,
  supplierRfqs: () => [...fiyatlamaKeys.all, "supplier-rfqs"] as const,
  supplierRfq: (id: number | string) =>
    [...fiyatlamaKeys.all, "supplier-rfq", String(id)] as const,
  supplierOffers: () => [...fiyatlamaKeys.all, "supplier-offers"] as const,
  buyerRfqs: () => [...fiyatlamaKeys.all, "buyer-rfqs"] as const,
};

async function loadSessionQuotesAndLocks(
  extraQuoteIds: number[] = []
): Promise<{ quotes: PriceQuote[]; locks: PriceLock[] }> {
  const quoteIds = [...new Set([...readIds(QUOTE_KEY), ...extraQuoteIds])];
  const lockIds = readIds(LOCK_KEY);

  const quoteSettled = await Promise.allSettled(
    quoteIds.map((id) => fiyatlamaService.getQuote(id))
  );
  const lockSettled = await Promise.allSettled(
    lockIds.map((id) => fiyatlamaService.getPriceLock(id))
  );

  const quotes = quoteSettled
    .filter((r): r is PromiseFulfilledResult<PriceQuote> => r.status === "fulfilled")
    .map((r) => r.value);
  const locks = lockSettled
    .filter((r): r is PromiseFulfilledResult<PriceLock> => r.status === "fulfilled")
    .map((r) => r.value);

  writeIds(
    QUOTE_KEY,
    quotes.map((q) => q.id)
  );
  writeIds(
    LOCK_KEY,
    locks.map((l) => l.id)
  );

  return { quotes, locks };
}

/** OpenAPI'de quote/lock listesi yok; oturum id + cart quote_id. */
export function useSessionQuotesAndLocksQuery(extraQuoteIds: number[] = []) {
  return useQuery({
    queryKey: fiyatlamaKeys.session(extraQuoteIds),
    queryFn: () => loadSessionQuotesAndLocks(extraQuoteIds),
  });
}

/** Geriye uyum: pricing-quotes-view için. */
export function useSessionQuotesAndLocks() {
  const qc = useQueryClient();
  const query = useSessionQuotesAndLocksQuery();

  const refresh = useCallback(
    async (extraQuoteIds: number[] = []) => {
      writeIds(QUOTE_KEY, [...readIds(QUOTE_KEY), ...extraQuoteIds]);
      await qc.invalidateQueries({ queryKey: fiyatlamaKeys.all });
      return qc.fetchQuery({
        queryKey: fiyatlamaKeys.session(extraQuoteIds),
        queryFn: () => loadSessionQuotesAndLocks(extraQuoteIds),
      });
    },
    [qc]
  );

  return {
    quotes: query.data?.quotes ?? [],
    locks: query.data?.locks ?? [],
    loading: query.isLoading || query.isFetching,
    error: query.error
      ? query.error instanceof Error
        ? query.error.message
        : "Fiyatlama kayıtları alınamadı."
      : null,
    refresh,
    setError: (_msg: string | null) => {
      /* Query hataları query.error üzerinden; satır içi set için no-op uyum. */
    },
  };
}

export function useCreatePriceLockMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (quoteId: number) => fiyatlamaService.createPriceLock(quoteId),
    onSuccess: (lock) => {
      rememberLockId(lock.id);
      void qc.invalidateQueries({ queryKey: fiyatlamaKeys.all });
    },
  });
}

export function useSupplierRfqsQuery(enabled = true) {
  return useQuery({
    queryKey: fiyatlamaKeys.supplierRfqs(),
    queryFn: () => fiyatlamaService.getSupplierRfqs(),
    enabled,
  });
}

export function useSupplierRfqQuery(id: number | string | undefined, enabled = true) {
  return useQuery({
    queryKey: fiyatlamaKeys.supplierRfq(id ?? ""),
    queryFn: () => fiyatlamaService.getSupplierRfq(id!),
    enabled: Boolean(id) && enabled,
  });
}

export function useSupplierOffersQuery(enabled = true) {
  return useQuery({
    queryKey: fiyatlamaKeys.supplierOffers(),
    queryFn: () => fiyatlamaService.getSupplierOffers(),
    enabled,
  });
}

export function useBuyerRfqsQuery(enabled = true) {
  return useQuery({
    queryKey: fiyatlamaKeys.buyerRfqs(),
    queryFn: () => fiyatlamaService.getBuyerRfqs(),
    enabled,
  });
}

export function useBuyerRfqQuery(id: number | string | undefined, enabled = true) {
  return useQuery({
    queryKey: [...fiyatlamaKeys.buyerRfqs(), "detail", String(id ?? "")] as const,
    queryFn: () => fiyatlamaService.getBuyerRfqDetail(id!),
    enabled: Boolean(id) && enabled,
  });
}

export function useFiyatlamaInvalidate() {
  const qc = useQueryClient();
  return () => void qc.invalidateQueries({ queryKey: fiyatlamaKeys.all });
}
