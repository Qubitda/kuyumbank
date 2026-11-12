"use client";

import { useQuery } from "@tanstack/react-query";
import { raporlarService } from "../services";

export const raporlarKeys = {
  all: ["raporlar"] as const,
  commercial: (from: string, to: string) =>
    [...raporlarKeys.all, "commercial", from, to] as const,
  behavior: (from: string, to: string) =>
    [...raporlarKeys.all, "behavior", from, to] as const,
  anomaly: (esik: string) => [...raporlarKeys.all, "anomaly", esik] as const,
};

export function useCommercialOrdersQuery(
  dateFrom: string,
  dateTo: string,
  enabled = true
) {
  return useQuery({
    queryKey: raporlarKeys.commercial(dateFrom, dateTo),
    queryFn: () =>
      raporlarService.getCommercialOrders({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
    enabled,
  });
}

export function useBuyerBehaviorQuery(
  dateFrom: string,
  dateTo: string,
  enabled = true
) {
  return useQuery({
    queryKey: raporlarKeys.behavior(dateFrom, dateTo),
    queryFn: () =>
      raporlarService.getBuyerBehavior({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
    enabled,
  });
}

export function useRevenueAnomaliesQuery(esikCiro: string, enabled = true) {
  return useQuery({
    queryKey: raporlarKeys.anomaly(esikCiro),
    queryFn: () => raporlarService.getRevenueAnomalies(esikCiro),
    enabled: enabled && Boolean(esikCiro.trim()),
  });
}
