"use client";

import { useEffect, useState } from "react";
import { kaliteService } from "../services";
import type { OpsInspection } from "../types";

export function useInspections() {
  const [inspections, setInspections] = useState<OpsInspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    kaliteService
      .getInspections()
      .then((data) => setInspections(data?.results || []))
      .catch((err) => setError(err instanceof Error ? err.message : "Kalite verileri alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { inspections, loading, error };
}
