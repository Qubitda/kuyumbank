"use client";

import { useQuery } from "@tanstack/react-query";
import type { Capabilities } from "@/lib/api/types";
import { dashboardService } from "../services";
import type { DashboardFilters } from "../types";

export const dashboardKeys = {
  all: ["dashboard"] as const,
  snapshot: (filters: DashboardFilters, capKey: string) =>
    [...dashboardKeys.all, "snapshot", capKey, filters] as const,
};

function capKey(caps: Capabilities | null | undefined): string {
  if (!caps) return "anon";
  return Object.entries(caps)
    .filter(([, v]) => Boolean(v))
    .map(([k]) => k)
    .sort()
    .join(",");
}

export function useDashboardSnapshotQuery(
  caps: Capabilities | null | undefined,
  filters: DashboardFilters,
  enabled = true
) {
  return useQuery({
    queryKey: dashboardKeys.snapshot(filters, capKey(caps)),
    queryFn: () => dashboardService.loadSnapshot(caps, filters),
    enabled,
  });
}
