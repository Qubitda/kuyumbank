"use client";

import { useEffect, useState } from "react";
import { firmalarService } from "../services";
import type { OrgUnit } from "../types";

export function useOrgUnits() {
  const [data, setData] = useState<OrgUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    firmalarService
      .getOrgUnits()
      .then((res) => setData(res?.results || []))
      .catch((err) => setError(err instanceof Error ? err.message : "Veri alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
