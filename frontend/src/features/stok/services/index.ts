import { apiFetch } from "@/lib/api/client";
import type { StockBalance } from "../types";

export const stokService = {
  getSupplierStock(): Promise<StockBalance[]> {
    return apiFetch<StockBalance[]>("/supplier/stock/");
  },
  adjustStock(data: { varyant_id: number; miktar: string; aciklama?: string }): Promise<void> {
    return apiFetch<void>("/supplier/stock/adjustments/", {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
};
