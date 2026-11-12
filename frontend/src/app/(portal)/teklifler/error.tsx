"use client";

import { DomainError } from "@/components/route-states";

export default function TekliflerError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Tedarikçi Teklif Portalı" error={error} reset={reset} />;
}
