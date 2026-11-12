"use client";

import { formatMoney } from "@/lib/format";
import { usePiyasaPano } from "../hooks";

/**
 * Header borsa şeridi — yalnız Buyer PiyasaPano alanları.
 * Marj / maliyet / tedarikçi gösterilmez.
 */
export function PiyasaPanoStrip() {
  const q = usePiyasaPano();
  const rows = q.data?.satirlar ?? [];

  if (q.isError) {
    return (
      <div
        className="hidden md:flex items-center gap-2 overflow-hidden text-[11px] text-muted-foreground"
        aria-live="polite"
      >
        <span className="font-mono">Borsa</span>
        <span>—</span>
      </div>
    );
  }

  if (q.isLoading && rows.length === 0) {
    return (
      <div
        className="hidden md:flex items-center gap-2 text-[11px] text-muted-foreground"
        aria-busy="true"
      >
        <span className="font-mono">Borsa</span>
        <span className="animate-pulse">…</span>
      </div>
    );
  }

  if (rows.length === 0) {
    return null;
  }

  return (
    <div
      className="hidden lg:flex min-w-0 max-w-[42vw] items-center gap-3 overflow-x-auto"
      aria-label="Piyasa panosu"
    >
      {rows.slice(0, 6).map((s) => (
        <div
          key={s.kod}
          className="shrink-0 flex items-baseline gap-1.5 border-l border-border pl-3 first:border-l-0 first:pl-0"
        >
          <span className="font-mono text-[10px] uppercase text-muted-foreground">
            {s.kod}
          </span>
          <span className="font-mono text-xs tabular-nums text-foreground">
            {formatMoney(s.fiyat, s.para_birimi)}
          </span>
          <span className="font-mono text-[9px] text-muted-foreground">
            {s.kaynak}
          </span>
        </div>
      ))}
    </div>
  );
}
