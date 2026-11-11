import { apiFetch } from "@/lib/api/client";
import type { BuyerCatalogPage, BuyerCatalogDetail } from "../types";

export const urunlerService = {
  getCatalog(params?: Record<string, string>): Promise<BuyerCatalogPage> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch<BuyerCatalogPage>(`/catalog/${query}`);
  },
  getProductDetail(id: number | string): Promise<BuyerCatalogDetail> {
    return apiFetch<BuyerCatalogDetail>(`/catalog/${id}/`);
  },
};
