import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  CariHesap,
  CreditInfo,
  FinanceSummary,
  LedgerEntry,
  PaymentIntent,
} from "../types";

export const finansService = {
  getMyFinance(paraBirimi = "TRY"): Promise<FinanceSummary> {
    return apiFetch<FinanceSummary>(
      `/finance/me/?para_birimi=${encodeURIComponent(paraBirimi)}`
    );
  },
  getMyCredit(paraBirimi = "TRY"): Promise<CreditInfo> {
    return apiFetch<CreditInfo>(
      `/credit/me/?para_birimi=${encodeURIComponent(paraBirimi)}`
    );
  },
  getCariList(params?: Record<string, string>): Promise<Paginated<CariHesap>> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch<Paginated<CariHesap>>(`/finance/cari/${query}`);
  },
  getLedger(params?: Record<string, string>): Promise<Paginated<LedgerEntry>> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch<Paginated<LedgerEntry>>(`/finance/ledger/${query}`);
  },
  createPaymentIntent(orderId: number): Promise<PaymentIntent> {
    return apiFetch<PaymentIntent>("/payments/intents/", {
      method: "POST",
      body: { order_id: orderId },
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
