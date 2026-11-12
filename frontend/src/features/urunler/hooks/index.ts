"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { urunlerService } from "../services";
import type { OpsProductCreateRequest, OpsProductVariantCreateRequest } from "../types";

export const urunlerKeys = {
  all: ["urunler"] as const,
  catalog: (filters?: Record<string, string | undefined>) =>
    [...urunlerKeys.all, "catalog", filters ?? {}] as const,
  catalogDetail: (id: number | string) =>
    [...urunlerKeys.all, "catalog", "detail", String(id)] as const,
  ops: (filters?: Record<string, string | undefined>) =>
    [...urunlerKeys.all, "ops", filters ?? {}] as const,
  opsDetail: (id: number | string) =>
    [...urunlerKeys.all, "ops", "detail", String(id)] as const,
};

export function useCatalogQuery(
  filters?: Record<string, string | undefined>,
  enabled = true
) {
  return useQuery({
    queryKey: urunlerKeys.catalog(filters),
    queryFn: () => urunlerService.getCatalog(filters),
    enabled,
  });
}

export function useCatalogDetailQuery(id: number | string | undefined, enabled = true) {
  return useQuery({
    queryKey: urunlerKeys.catalogDetail(id ?? ""),
    queryFn: () => urunlerService.getProductDetail(id!),
    enabled: Boolean(id) && enabled,
  });
}

export function useOpsProductsQuery(
  filters?: Record<string, string | undefined>,
  enabled = true
) {
  return useQuery({
    queryKey: urunlerKeys.ops(filters),
    queryFn: () => urunlerService.getOpsProducts(filters),
    enabled,
  });
}

export function useOpsProductQuery(id: number | string | undefined, enabled = true) {
  return useQuery({
    queryKey: urunlerKeys.opsDetail(id ?? ""),
    queryFn: () => urunlerService.getOpsProduct(id!),
    enabled: Boolean(id) && enabled,
  });
}

export function useCreateOpsProductMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: OpsProductCreateRequest) =>
      urunlerService.createOpsProduct(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: urunlerKeys.all });
    },
  });
}

export function useOpsProductActionMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: {
      action:
        | "submit"
        | "approve"
        | "reject"
        | "publish"
        | "unpublish"
        | "addVariant";
      id: number | string;
      neden?: string;
      variant?: OpsProductVariantCreateRequest;
      durum?: string;
    }) => {
      switch (input.action) {
        case "submit":
          return urunlerService.submitOpsProduct(input.id);
        case "approve":
          return urunlerService.approveOpsProduct(input.id);
        case "reject":
          return urunlerService.rejectOpsProduct(input.id, input.neden || "");
        case "publish":
          return urunlerService.publishOpsProduct(input.id, input.durum);
        case "unpublish":
          return urunlerService.unpublishOpsProduct(input.id);
        case "addVariant":
          return urunlerService.addOpsVariant(input.id, input.variant!);
      }
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: urunlerKeys.all });
    },
  });
}
