"use client";

import { useEffect, useState } from "react";
import { lojistikService } from "../services";
import type { OpsShipment } from "../types";

export function useShipments() {
  const [shipments, setShipments] = useState<OpsShipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    lojistikService
      .getShipments()
      .then((data) => setShipments(data?.results || []))
      .catch((err) => setError(err instanceof Error ? err.message : "Sevkiyat bilgisi alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { shipments, loading, error };
}
