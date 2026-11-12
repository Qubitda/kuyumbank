"use client";

import { cn } from "@/lib/utils";

const STEPS = [
  { key: "TASLAK", label: "Taslak" },
  { key: "GONDERILDI", label: "Gönderildi" },
  { key: "TEKLIF_ALINDI", label: "Teklif alındı" },
  { key: "KAPANDI", label: "Kapandı" },
] as const;

function stepIndex(durum: string): number {
  const i = STEPS.findIndex((s) => s.key === durum);
  if (durum === "IPTAL") return -1;
  return i;
}

export function RfqStatusTracker({ durum }: { durum: string }) {
  if (durum === "IPTAL") {
    return (
      <p className="text-xs text-destructive font-medium" role="status">
        İptal edildi
      </p>
    );
  }

  const active = stepIndex(durum);
  return (
    <ol className="flex flex-wrap items-center gap-1.5" aria-label="RFQ durum takibi">
      {STEPS.map((s, idx) => {
        const done = active >= 0 && idx <= active;
        const current = idx === active;
        return (
          <li key={s.key} className="flex items-center gap-1.5">
            {idx > 0 ? (
              <span className="text-muted-foreground/40" aria-hidden>
                →
              </span>
            ) : null}
            <span
              className={cn(
                "rounded-[4px] border px-2 py-0.5 text-[10px] font-mono",
                done
                  ? "border-foreground/30 bg-secondary text-foreground"
                  : "border-border text-muted-foreground",
                current && "font-semibold"
              )}
            >
              {s.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
