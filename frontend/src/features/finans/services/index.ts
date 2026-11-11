import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export function fetchFinanceMe(): Promise<
  components["schemas"]["BuyerFinanceSummary"]
> {
  return apiFetch("/finance/me/");
}

export function fetchCreditMe(): Promise<components["schemas"]["BuyerCredit"]> {
  return apiFetch("/credit/me/");
}

export function createPaymentIntent(
  body: components["schemas"]["PaymentIntentCreateRequest"],
  idempotencyKey: string,
): Promise<components["schemas"]["BuyerPaymentIntent"]> {
  return apiFetch("/payments/intents/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}
