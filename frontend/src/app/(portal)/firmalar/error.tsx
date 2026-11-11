"use client";

import { DomainError } from "@/components/route-states";

export default function FirmalarError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Firmalar" error={error} reset={reset} />;
}
