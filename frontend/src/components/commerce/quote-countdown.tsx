"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

function remainingMs(expiresAt: string, now: number): number {
  const end = new Date(expiresAt).getTime();
  if (Number.isNaN(end)) return 0;
  return Math.max(0, end - now);
}

function formatRemain(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function isQuoteExpired(
  expiresAt: string | null | undefined,
  now = Date.now()
): boolean {
  if (!expiresAt) return false;
  return remainingMs(expiresAt, now) <= 0;
}

interface QuoteCountdownProps {
  expiresAt?: string | null;
  className?: string;
  onExpired?: () => void;
}

/** Quote / lock TTL geri sayımı — para aritmetiği yok. */
export function QuoteCountdown({
  expiresAt,
  className,
  onExpired,
}: QuoteCountdownProps) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!expiresAt) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [expiresAt]);

  useEffect(() => {
    if (!expiresAt) return;
    if (remainingMs(expiresAt, now) <= 0) onExpired?.();
  }, [expiresAt, now, onExpired]);

  if (!expiresAt) {
    return (
      <span className={cn("text-xs text-muted-foreground", className)}>
        Süresiz
      </span>
    );
  }

  const left = remainingMs(expiresAt, now);
  if (left <= 0) {
    return (
      <span
        className={cn(
          "font-mono text-xs tabular-nums text-destructive",
          className
        )}
        role="status"
      >
        Süresi doldu
      </span>
    );
  }

  const urgent = left < 60_000;
  return (
    <span
      className={cn(
        "font-mono text-xs tabular-nums",
        urgent ? "text-destructive" : "text-muted-foreground",
        className
      )}
      role="timer"
      aria-live="polite"
      title={expiresAt}
    >
      {formatRemain(left)}
    </span>
  );
}
