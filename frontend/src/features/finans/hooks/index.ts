"use client";

import { useEffect, useState } from "react";
import { unwrapResults } from "@/lib/api/client";
import { finansService } from "../services";
import type { CariHesap, CreditInfo } from "../types";

export function useFinance() {
  const [cariList, setCariList] = useState<CariHesap[]>([]);
  const [credit, setCredit] = useState<CreditInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.allSettled([finansService.getCariList(), finansService.getMyCredit()])
      .then(([cariRes, creditRes]) => {
        if (cariRes.status === "fulfilled") {
          setCariList(unwrapResults(cariRes.value));
        }
        if (creditRes.status === "fulfilled") {
          setCredit(creditRes.value);
        }
        if (cariRes.status === "rejected" && creditRes.status === "rejected") {
          setError("Finans bilgisi alınamadı");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  return { cariList, credit, loading, error };
}
