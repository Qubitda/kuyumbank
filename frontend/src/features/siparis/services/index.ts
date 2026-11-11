import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type Cart = components["schemas"]["BuyerCart"];
type Order = components["schemas"]["BuyerOrder"];
type OrderPage = components["schemas"]["BuyerOrderPage"];
type Rfq = components["schemas"]["Rfq"];
type RfqMatch = components["schemas"]["RfqMatch"];
type RfqMatchCandidates = components["schemas"]["RfqMatchCandidates"];
type RfqMatchList = components["schemas"]["RfqMatchList"];

export function getMyCart(): Promise<Cart> {
  return apiFetch<Cart>("/carts/me/");
}

export function addCartLine(
  body: components["schemas"]["CartLineCreateRequest"],
  idempotencyKey: string,
): Promise<Cart> {
  return apiFetch<Cart>("/carts/me/lines/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}

export function checkout(idempotencyKey: string): Promise<
  components["schemas"]["CheckoutResult"]
> {
  return apiFetch("/checkouts/", {
    method: "POST",
    body: {},
    idempotencyKey,
  });
}

export function orderFromCheckout(
  checkoutId: number,
  idempotencyKey: string,
): Promise<Order> {
  return apiFetch<Order>("/orders/from-checkout/", {
    method: "POST",
    body: { checkout_id: checkoutId },
    idempotencyKey,
  });
}

export function listOrders(): Promise<OrderPage> {
  return apiFetch<OrderPage>("/orders/");
}

export function getOrder(id: number): Promise<Order> {
  return apiFetch<Order>(`/orders/${id}/`);
}

export function createRfq(
  body: components["schemas"]["RfqCreateRequest"],
  idempotencyKey: string,
): Promise<Rfq> {
  return apiFetch<Rfq>("/rfqs/", { method: "POST", body, idempotencyKey });
}

export function listRfqMatchCandidates(
  lineId: number,
): Promise<RfqMatchCandidates> {
  return apiFetch<RfqMatchCandidates>(
    `/ops/rfq-lines/${lineId}/match-candidates/`,
  );
}

export function listRfqMatches(lineId: number): Promise<RfqMatchList> {
  return apiFetch<RfqMatchList>(`/ops/rfq-lines/${lineId}/matches/`);
}

export function createRfqMatch(
  lineId: number,
  body: components["schemas"]["RfqMatchCreateRequest"],
  idempotencyKey: string,
): Promise<RfqMatch> {
  return apiFetch<RfqMatch>(`/ops/rfq-lines/${lineId}/matches/`, {
    method: "POST",
    body,
    idempotencyKey,
  });
}

export function approveRfqMatch(
  id: number,
  idempotencyKey: string,
): Promise<RfqMatch> {
  return apiFetch<RfqMatch>(`/ops/rfq-matches/${id}/approve/`, {
    method: "POST",
    body: {},
    idempotencyKey,
  });
}

export function rejectRfqMatch(
  id: number,
  neden: string,
  idempotencyKey: string,
): Promise<RfqMatch> {
  return apiFetch<RfqMatch>(`/ops/rfq-matches/${id}/reject/`, {
    method: "POST",
    body: { neden },
    idempotencyKey,
  });
}
