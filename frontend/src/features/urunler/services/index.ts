import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type CatalogPage = components["schemas"]["BuyerCatalogPage"];
type CatalogDetail = components["schemas"]["BuyerCatalogDetail"];

export type SalesChannel = {
  id: number;
  kod: string;
  ad: string;
  quote_ttl_saniye?: number;
};

export type SalesChannelPage = {
  count: number;
  results: SalesChannel[];
  server_now?: string;
};

export function listCatalog(query?: {
  page?: number;
  search?: string;
}): Promise<CatalogPage> {
  const qs = new URLSearchParams();
  if (query?.page) qs.set("page", String(query.page));
  if (query?.search) qs.set("q", query.search);
  const suffix = qs.toString() ? `?${qs}` : "";
  return apiFetch<CatalogPage>(`/catalog/${suffix}`);
}

export function getCatalogItem(id: number): Promise<CatalogDetail> {
  return apiFetch<CatalogDetail>(`/catalog/${id}/`);
}

/** FE keşif — quote için zorunlu satis_kanali_id (BACKEND_MAP). */
export function listSalesChannels(): Promise<SalesChannelPage> {
  return apiFetch<SalesChannelPage>("/sales-channels/");
}
