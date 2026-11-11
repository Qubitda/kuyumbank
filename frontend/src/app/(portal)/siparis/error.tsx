"use client";

import { DomainError } from "@/components/route-states";

export default function SiparisError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Siparişler" error={error} reset={reset} />;
}
