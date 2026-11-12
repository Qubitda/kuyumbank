"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { kaliteService } from "../services";
import type { InspectionMeasurementRequest } from "../types";

export const kaliteKeys = {
  all: ["kalite"] as const,
  list: () => [...kaliteKeys.all, "list"] as const,
  detail: (id: number | string) =>
    [...kaliteKeys.all, "detail", String(id)] as const,
};

function invalidateKalite(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: kaliteKeys.all });
}

export function useInspectionsQuery(enabled = true) {
  return useQuery({
    queryKey: kaliteKeys.list(),
    queryFn: async () => {
      const page = await kaliteService.getInspections();
      return page.results ?? [];
    },
    enabled,
  });
}

export function useStartInspectionMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => kaliteService.startInspection(id),
    onSuccess: () => invalidateKalite(qc),
  });
}

export function usePassInspectionMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => kaliteService.passInspection(id),
    onSuccess: () => invalidateKalite(qc),
  });
}

export function useFailInspectionMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => kaliteService.failInspection(id),
    onSuccess: () => invalidateKalite(qc),
  });
}

export function useCancelInspectionMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => kaliteService.cancelInspection(id),
    onSuccess: () => invalidateKalite(qc),
  });
}

export function useAddMeasurementMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: InspectionMeasurementRequest;
    }) => kaliteService.addMeasurement(id, data),
    onSuccess: () => invalidateKalite(qc),
  });
}
