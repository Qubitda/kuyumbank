"use client";

import { DomainError } from "@/components/route-states";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Stok" error={error} reset={reset} />;
}
