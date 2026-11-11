import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type CatalogPage = components["schemas"]["BuyerCatalogPage"];
type CatalogDetail = components["schemas"]["BuyerCatalogDetail"];

export function listCatalog(query?: {
  page?: number;
  search?: string;
}): Promise<CatalogPage> {
  const qs = new URLSearchParams();
  if (query?.page) qs.set("page", String(query.page));
  if (query?.search) qs.set("search", query.search);
  const suffix = qs.toString() ? `?${qs}` : "";
  return apiFetch<CatalogPage>(`/catalog/${suffix}`);
}

export function getCatalogItem(id: number): Promise<CatalogDetail> {
  return apiFetch<CatalogDetail>(`/catalog/${id}/`);
}
