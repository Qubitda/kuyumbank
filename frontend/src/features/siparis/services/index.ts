import { apiFetch } from "@/lib/api/client";
import type { BuyerCart, BuyerOrder, CheckoutRequest } from "../types";

export const siparisService = {
  getMyCart(): Promise<BuyerCart> {
    return apiFetch<BuyerCart>("/carts/me/");
  },
  addCartLine(quoteId: number, miktar: string): Promise<BuyerCart> {
    return apiFetch<BuyerCart>("/carts/me/lines/", {
      method: "POST",
      body: { quote_id: quoteId, miktar },
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  removeCartLine(lineId: number): Promise<void> {
    return apiFetch<void>(`/carts/me/lines/${lineId}/`, {
      method: "DELETE",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  checkout(data: CheckoutRequest = {}): Promise<BuyerOrder> {
    return apiFetch<BuyerOrder>("/checkouts/", {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  getOrders(): Promise<BuyerOrder[]> {
    return apiFetch<BuyerOrder[]>("/orders/");
  },
  getOrderDetail(id: number | string): Promise<BuyerOrder> {
    return apiFetch<BuyerOrder>(`/orders/${id}/`);
  },
  cancelOrder(id: number | string): Promise<BuyerOrder> {
    return apiFetch<BuyerOrder>(`/orders/${id}/cancel/`, {
      method: "POST",
      body: {},
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
};
