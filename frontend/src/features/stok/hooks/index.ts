"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { stokService } from "../services";
import type { StockAdjustmentRequest } from "../types";

export const stokKeys = {
  all: ["stok"] as const,
  supplier: () => [...stokKeys.all, "supplier"] as const,
};

export function useSupplierStockQuery(enabled = true) {
  return useQuery({
    queryKey: stokKeys.supplier(),
    queryFn: () => stokService.listSupplierStock(),
    enabled,
  });
}

export function useAdjustStockMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: StockAdjustmentRequest) => stokService.adjustStock(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: stokKeys.all });
    },
  });
}
