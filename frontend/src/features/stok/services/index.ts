import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export function listSupplierStock(): Promise<
  components["schemas"]["SupplierStockPage"]
> {
  return apiFetch("/supplier/stock/");
}

export function adjustSupplierStock(
  body: components["schemas"]["SupplierStockAdjustRequest"],
  idempotencyKey: string,
): Promise<unknown> {
  return apiFetch("/supplier/stock/adjustments/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}
