"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/auth";
import { belgelerService } from "../services";
import type { DocumentItem, DocumentsSnapshot } from "../types";

export function useDocuments() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [errors, setErrors] = useState<DocumentsSnapshot["errors"]>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const snap = await belgelerService.getDocuments(user?.capabilities);
      setDocuments(snap.items);
      setErrors(snap.errors);
      const failKeys = Object.keys(snap.errors);
      if (snap.items.length === 0 && failKeys.length > 0) {
        setError(Object.values(snap.errors).filter(Boolean).join(" · "));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Belgeler alınamadı.");
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [user?.capabilities]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { documents, errors, loading, error, refresh };
}
