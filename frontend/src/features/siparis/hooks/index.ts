"use client";

import { useEffect, useState } from "react";
import { unwrapResults } from "@/lib/api/client";
import { siparisService } from "../services";
import type { BuyerOrder } from "../types";

export function useOrders() {
  const [orders, setOrders] = useState<BuyerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    siparisService
      .getOrders()
      .then((page) => setOrders(unwrapResults(page)))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Siparişler alınamadı")
      )
      .finally(() => setLoading(false));
  }, []);

  return { orders, loading, error };
}
