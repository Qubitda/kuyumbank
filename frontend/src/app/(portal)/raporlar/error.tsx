"use client";

import { DomainError } from "@/components/route-states";

export default function RaporlarError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Ticari Raporlar & Analitik" error={error} reset={reset} />;
}
