import { apiFetch } from "@/lib/api/client";
import type { PriceQuote, PriceLock } from "../types";

export const fiyatlamaService = {
  getQuotes(): Promise<PriceQuote[]> {
    return apiFetch<PriceQuote[]>("/quotes/");
  },
  getQuote(id: number | string): Promise<PriceQuote> {
    return apiFetch<PriceQuote>(`/quotes/${id}/`);
  },
  getPriceLocks(): Promise<PriceLock[]> {
    return apiFetch<PriceLock[]>("/price-locks/");
  },
  createQuote(data: { varyant_id: number; satis_kanali_id?: number; para_birimi?: string }): Promise<PriceQuote> {
    return apiFetch<PriceQuote>("/quotes/", {
      method: "POST",
      body: {
        varyant_id: data.varyant_id,
        satis_kanali_id: data.satis_kanali_id || 1,
        para_birimi: data.para_birimi || "TRY",
      },
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  createPriceLock(quoteId: number): Promise<PriceLock> {
    return apiFetch<PriceLock>("/price-locks/", {
      method: "POST",
      body: { quote_id: quoteId },
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
};
