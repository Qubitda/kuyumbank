"use client";

import { DomainError } from "@/components/route-states";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Lojistik" error={error} reset={reset} />;
}
