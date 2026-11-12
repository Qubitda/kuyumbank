import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type {
  BuyerCatalogPage,
  BuyerCatalogDetail,
  OpsProduct,
  OpsProductPage,
  OpsProductCreateRequest,
  OpsProductVariant,
  OpsProductVariantCreateRequest,
} from "../types";

function qs(params?: Record<string, string | undefined>): string {
  if (!params) return "";
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null && String(v).trim() !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const urunlerService = {
  getCatalog(params?: Record<string, string | undefined>): Promise<BuyerCatalogPage> {
    return apiFetch<BuyerCatalogPage>(`/catalog/${qs(params)}`);
  },
  getProductDetail(id: number | string): Promise<BuyerCatalogDetail> {
    return apiFetch<BuyerCatalogDetail>(`/catalog/${id}/`);
  },

  getOpsProducts(params?: Record<string, string | undefined>): Promise<OpsProductPage> {
    return apiFetch<OpsProductPage>(`/ops/products/${qs(params)}`);
  },
  getOpsProduct(id: number | string): Promise<OpsProduct> {
    return apiFetch<OpsProduct>(`/ops/products/${id}/`);
  },
  createOpsProduct(data: OpsProductCreateRequest): Promise<OpsProduct> {
    return apiFetch<OpsProduct>("/ops/products/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  addOpsVariant(
    productId: number | string,
    data: OpsProductVariantCreateRequest
  ): Promise<OpsProductVariant> {
    return apiFetch<OpsProductVariant>(`/ops/products/${productId}/variants/`, {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  submitOpsProduct(id: number | string): Promise<OpsProduct> {
    return apiFetch<OpsProduct>(`/ops/products/${id}/submit/`, {
      method: "POST",
      body: {},
      idempotencyKey: newIdempotencyKey(),
    });
  },
  approveOpsProduct(id: number | string): Promise<OpsProduct> {
    return apiFetch<OpsProduct>(`/ops/products/${id}/approve/`, {
      method: "POST",
      body: {},
      idempotencyKey: newIdempotencyKey(),
    });
  },
  rejectOpsProduct(id: number | string, neden: string): Promise<OpsProduct> {
    return apiFetch<OpsProduct>(`/ops/products/${id}/reject/`, {
      method: "POST",
      body: { neden },
      idempotencyKey: newIdempotencyKey(),
    });
  },
  publishOpsProduct(id: number | string, durum = "aktif"): Promise<OpsProduct> {
    return apiFetch<OpsProduct>(`/ops/products/${id}/publish/`, {
      method: "POST",
      body: { durum },
      idempotencyKey: newIdempotencyKey(),
    });
  },
  unpublishOpsProduct(id: number | string): Promise<OpsProduct> {
    return apiFetch<OpsProduct>(`/ops/products/${id}/unpublish/`, {
      method: "POST",
      body: {},
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
