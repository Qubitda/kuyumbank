"use client";

import { useEffect, useState } from "react";
import { belgelerService } from "../services";
import type { DocumentItem } from "../types";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    belgelerService
      .getDocuments()
      .then(setDocuments)
      .catch((err) => setError(err instanceof Error ? err.message : "Belgeler alınamadı"))
      .finally(() => setLoading(false));
  }, []);

  return { documents, loading, error };
}
