"use client";

import { DomainError } from "@/components/route-states";

export default function BelgelerError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Belgeler" error={error} reset={reset} />;
}
