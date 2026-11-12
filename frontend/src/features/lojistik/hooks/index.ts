"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { lojistikService } from "../services";
import type { DispatchShipmentRequest, PodRequest } from "../types";

export const lojistikKeys = {
  all: ["lojistik"] as const,
  opsShipments: () => [...lojistikKeys.all, "ops-shipments"] as const,
  returns: () => [...lojistikKeys.all, "returns"] as const,
  buyerShipments: () => [...lojistikKeys.all, "buyer-shipments"] as const,
};

function invalidateLojistik(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: lojistikKeys.all });
}

export function useOpsShipmentsQuery(enabled = true) {
  return useQuery({
    queryKey: lojistikKeys.opsShipments(),
    queryFn: async () => {
      const page = await lojistikService.getShipments();
      return page.results ?? [];
    },
    enabled,
  });
}

export function useReturnsQuery(enabled = true) {
  return useQuery({
    queryKey: lojistikKeys.returns(),
    queryFn: async () => {
      const page = await lojistikService.getReturns();
      return page.results ?? [];
    },
    enabled,
  });
}

export function usePrepareShipmentMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => lojistikService.prepareShipment(id),
    onSuccess: () => invalidateLojistik(qc),
  });
}

export function useDispatchShipmentMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: DispatchShipmentRequest;
    }) => lojistikService.dispatchShipment(id, data),
    onSuccess: () => invalidateLojistik(qc),
  });
}

export function useDeliverShipmentMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => lojistikService.deliverShipment(id),
    onSuccess: () => invalidateLojistik(qc),
  });
}

export function useCancelShipmentMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => lojistikService.cancelShipment(id),
    onSuccess: () => invalidateLojistik(qc),
  });
}

export function useSubmitPodMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PodRequest }) =>
      lojistikService.submitPod(id, data),
    onSuccess: () => invalidateLojistik(qc),
  });
}

export function useApproveReturnMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => lojistikService.approveReturn(id),
    onSuccess: () => invalidateLojistik(qc),
  });
}

export function useMahsupReturnMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => lojistikService.mahsupReturn(id),
    onSuccess: () => invalidateLojistik(qc),
  });
}
