"use client";

import { DomainError } from "@/components/route-states";

export default function TanimlarError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Tanımlar" error={error} reset={reset} />;
}
