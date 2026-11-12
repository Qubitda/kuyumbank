"use client";

import { useQuery } from "@tanstack/react-query";
import { piyasaService } from "../services";
import type { PiyasaOlcek } from "../types";

export const piyasaKeys = {
  all: ["piyasa"] as const,
  pano: (olcek?: PiyasaOlcek) =>
    [...piyasaKeys.all, "pano", olcek ?? "ALL"] as const,
};

/** Canlı/LKG board — 30s refetch; marj alanı yok. */
export function usePiyasaPano(olcek?: PiyasaOlcek) {
  return useQuery({
    queryKey: piyasaKeys.pano(olcek),
    queryFn: () => piyasaService.getPano(olcek),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}
