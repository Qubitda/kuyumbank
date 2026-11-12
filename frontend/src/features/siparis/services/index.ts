import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  BuyerCart,
  BuyerOrder,
  BulkOrderResult,
  CheckoutResult,
} from "../types";

export const siparisService = {
  getMyCart(): Promise<BuyerCart> {
    return apiFetch<BuyerCart>("/carts/me/");
  },
  addCartLine(quoteId: number, miktar: string): Promise<BuyerCart> {
    return apiFetch<BuyerCart>("/carts/me/lines/", {
      method: "POST",
      body: { quote_id: quoteId, miktar },
      idempotencyKey: newIdempotencyKey(),
    });
  },
  updateCartLine(lineId: number, miktar: string): Promise<BuyerCart> {
    return apiFetch<BuyerCart>(`/carts/me/lines/${lineId}/`, {
      method: "PATCH",
      body: { miktar },
      idempotencyKey: newIdempotencyKey(),
    });
  },
  removeCartLine(lineId: number): Promise<void> {
    return apiFetch<void>(`/carts/me/lines/${lineId}/`, {
      method: "DELETE",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  /** POST /checkouts/ — EmptyRequest; adres alanları sözleşmede yok. */
  createCheckout(): Promise<CheckoutResult> {
    return apiFetch<CheckoutResult>("/checkouts/", {
      method: "POST",
      body: {},
      idempotencyKey: newIdempotencyKey(),
    });
  },
  createOrderFromCheckout(checkoutId: number): Promise<BuyerOrder> {
    return apiFetch<BuyerOrder>("/orders/from-checkout/", {
      method: "POST",
      body: { checkout_id: checkoutId },
      idempotencyKey: newIdempotencyKey(),
    });
  },
  /** Checkout + order oluşturma zinciri (OpenAPI B2). */
  async checkout(): Promise<BuyerOrder> {
    const result = await this.createCheckout();
    if (result.order_id) {
      return this.getOrderDetail(result.order_id);
    }
    return this.createOrderFromCheckout(result.checkout_id);
  },
  getOrders(params?: Record<string, string>): Promise<Paginated<BuyerOrder>> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch<Paginated<BuyerOrder>>(`/orders/${query}`);
  },
  getOrderDetail(id: number | string): Promise<BuyerOrder> {
    return apiFetch<BuyerOrder>(`/orders/${id}/`);
  },
  cancelOrder(id: number | string): Promise<BuyerOrder> {
    return apiFetch<BuyerOrder>(`/orders/${id}/cancel/`, {
      method: "POST",
      body: {},
      idempotencyKey: newIdempotencyKey(),
    });
  },
  reorder(id: number | string): Promise<BuyerCart> {
    return apiFetch<BuyerCart>(`/orders/${id}/reorder/`, {
      method: "POST",
      body: {},
      idempotencyKey: newIdempotencyKey(),
    });
  },
  createBulkOrder(data: {
    satis_kanali_id: number;
    rows?: Array<{ sku: string; miktar: string; birim?: string }>;
    csv?: string;
  }): Promise<BulkOrderResult> {
    return apiFetch<BulkOrderResult>("/bulk-orders/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
