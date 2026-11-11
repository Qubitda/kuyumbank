"use client";

import { DomainError } from "@/components/route-states";

export default function UrunlerError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Ürünler" error={error} reset={reset} />;
}
