import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type Quote = components["schemas"]["BuyerQuote"];
type PriceLock = components["schemas"]["BuyerPriceLock"];
type SupplierOffer = components["schemas"]["SupplierOffer"];
type SupplierOfferPage = components["schemas"]["SupplierOfferPage"];
type OfferCreate = components["schemas"]["SupplierOfferCreateRequest"];

export function createQuote(
  body: components["schemas"]["QuoteCreateRequest"],
  idempotencyKey: string,
): Promise<Quote> {
  return apiFetch<Quote>("/quotes/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}

export function getQuote(id: number): Promise<Quote> {
  return apiFetch<Quote>(`/quotes/${id}/`);
}

export function createPriceLock(
  body: components["schemas"]["PriceLockCreateRequest"],
  idempotencyKey: string,
): Promise<PriceLock> {
  return apiFetch<PriceLock>("/price-locks/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}

export function listSupplierOffers(): Promise<SupplierOfferPage> {
  return apiFetch<SupplierOfferPage>("/supplier/offers/");
}

export function createSupplierOffer(
  body: OfferCreate,
  idempotencyKey: string,
): Promise<SupplierOffer> {
  return apiFetch<SupplierOffer>("/supplier/offers/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}

export function submitSupplierOffer(
  id: number,
  idempotencyKey: string,
): Promise<SupplierOffer> {
  return apiFetch<SupplierOffer>(`/supplier/offers/${id}/submit/`, {
    method: "POST",
    body: {},
    idempotencyKey,
  });
}
