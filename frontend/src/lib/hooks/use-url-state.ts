import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Filtre/sayfalama değerlerini URL search params’ta tutar.
 */
export function useUrlState() {
  const [params, setParams] = useSearchParams();

  const get = useCallback(
    (key: string, fallback = "") => params.get(key) ?? fallback,
    [params]
  );

  const setMany = useCallback(
    (
      patch: Record<string, string | number | undefined | null>,
      opts?: { replace?: boolean }
    ) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          for (const [k, v] of Object.entries(patch)) {
            if (v === undefined || v === null || String(v).trim() === "") {
              next.delete(k);
            } else {
              next.set(k, String(v));
            }
          }
          return next;
        },
        { replace: opts?.replace ?? true }
      );
    },
    [setParams]
  );

  const page = useMemo(() => {
    const n = Number(get("page", "1"));
    return Number.isFinite(n) && n > 0 ? n : 1;
  }, [get]);

  return { params, get, setMany, page };
}
