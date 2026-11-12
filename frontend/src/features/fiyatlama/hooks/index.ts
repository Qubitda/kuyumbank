"use client";

import { useCallback, useState } from "react";
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

/** OpenAPI'de quote/lock listesi yok; oturumda üretilen id'ler + cart quote_id'leri. */
export function useSessionQuotesAndLocks() {
  const [quotes, setQuotes] = useState<PriceQuote[]>([]);
  const [locks, setLocks] = useState<PriceLock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (extraQuoteIds: number[] = []) => {
    setLoading(true);
    setError(null);
    try {
      const quoteIds = [...new Set([...readIds(QUOTE_KEY), ...extraQuoteIds])];
      const lockIds = readIds(LOCK_KEY);

      const quoteSettled = await Promise.allSettled(
        quoteIds.map((id) => fiyatlamaService.getQuote(id))
      );
      const lockSettled = await Promise.allSettled(
        lockIds.map((id) => fiyatlamaService.getPriceLock(id))
      );

      const nextQuotes = quoteSettled
        .filter((r): r is PromiseFulfilledResult<PriceQuote> => r.status === "fulfilled")
        .map((r) => r.value);
      const nextLocks = lockSettled
        .filter((r): r is PromiseFulfilledResult<PriceLock> => r.status === "fulfilled")
        .map((r) => r.value);

      setQuotes(nextQuotes);
      setLocks(nextLocks);
      writeIds(
        QUOTE_KEY,
        nextQuotes.map((q) => q.id)
      );
      writeIds(
        LOCK_KEY,
        nextLocks.map((l) => l.id)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fiyatlama kayıtları alınamadı.");
    } finally {
      setLoading(false);
    }
  }, []);

  return { quotes, locks, loading, error, refresh, setError };
}
