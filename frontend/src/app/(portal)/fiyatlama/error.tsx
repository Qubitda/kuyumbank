"use client";

import { DomainError } from "@/components/route-states";

export default function FiyatlamaError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Fiyatlama" error={error} reset={reset} />;
}
