"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { unwrapResults } from "@/lib/api/client";
import { siparisService } from "../services";

export const siparisKeys = {
  all: ["siparis"] as const,
  cart: () => [...siparisKeys.all, "cart"] as const,
  orders: (filters?: Record<string, string>) =>
    [...siparisKeys.all, "orders", filters ?? {}] as const,
  order: (id: number | string) =>
    [...siparisKeys.all, "order", String(id)] as const,
};

export function useCartQuery(enabled = true) {
  return useQuery({
    queryKey: siparisKeys.cart(),
    queryFn: () => siparisService.getMyCart(),
    enabled,
  });
}

export function useOrdersQuery(filters?: Record<string, string>, enabled = true) {
  return useQuery({
    queryKey: siparisKeys.orders(filters),
    queryFn: async () => {
      const page = await siparisService.getOrders(filters);
      return unwrapResults(page);
    },
    enabled,
  });
}

export function useOrderDetailQuery(id: number | string | undefined, enabled = true) {
  return useQuery({
    queryKey: siparisKeys.order(id ?? ""),
    queryFn: () => siparisService.getOrderDetail(id!),
    enabled: Boolean(id) && enabled,
  });
}

function invalidateCommerce(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: siparisKeys.all });
}

export function useAddCartLineMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ quoteId, miktar }: { quoteId: number; miktar: string }) =>
      siparisService.addCartLine(quoteId, miktar),
    onSuccess: () => invalidateCommerce(qc),
  });
}

export function useUpdateCartLineMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ lineId, miktar }: { lineId: number; miktar: string }) =>
      siparisService.updateCartLine(lineId, miktar),
    onSuccess: () => invalidateCommerce(qc),
  });
}

export function useRemoveCartLineMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (lineId: number) => siparisService.removeCartLine(lineId),
    onSuccess: () => invalidateCommerce(qc),
  });
}

export function useCheckoutMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => siparisService.checkout(),
    onSuccess: () => invalidateCommerce(qc),
  });
}

export function useCancelOrderMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number | string) => siparisService.cancelOrder(id),
    onSuccess: () => invalidateCommerce(qc),
  });
}

export function useBulkOrderMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      satis_kanali_id: number;
      rows?: Array<{ sku: string; miktar: string; birim?: string }>;
      csv?: string;
    }) => siparisService.createBulkOrder(data),
    onSuccess: () => invalidateCommerce(qc),
  });
}
