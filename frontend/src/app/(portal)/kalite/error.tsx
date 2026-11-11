"use client";

import { DomainError } from "@/components/route-states";

export default function KaliteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Kalite Kontrol" error={error} reset={reset} />;
}
