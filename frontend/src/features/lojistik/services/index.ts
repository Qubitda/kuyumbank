import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export function listShipments(): Promise<
  components["schemas"]["BuyerShipmentPage"]
> {
  return apiFetch("/shipments/");
}

export function listReturns(): Promise<
  components["schemas"]["BuyerReturnPage"]
> {
  return apiFetch("/returns/");
}

export function createReturn(
  body: components["schemas"]["ReturnCreateRequest"],
  idempotencyKey: string,
): Promise<components["schemas"]["BuyerReturn"]> {
  return apiFetch("/returns/", { method: "POST", body, idempotencyKey });
}
