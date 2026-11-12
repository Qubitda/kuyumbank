import { apiFetch } from "@/lib/api/client";
import type { PiyasaOlcek, PiyasaPano } from "../types";

export const piyasaService = {
  getPano(olcek?: PiyasaOlcek): Promise<PiyasaPano> {
    const q =
      olcek && String(olcek).trim()
        ? `?olcek=${encodeURIComponent(String(olcek).trim().toUpperCase())}`
        : "";
    return apiFetch<PiyasaPano>(`/piyasa/pano/${q}`);
  },
};
