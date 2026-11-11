"use client";

import { DomainError } from "@/components/route-states";

export default function FinansError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Finans" error={error} reset={reset} />;
}
