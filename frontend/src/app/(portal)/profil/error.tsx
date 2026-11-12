"use client";

import { DomainError } from "@/components/route-states";

export default function ProfilError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DomainError label="Profil ve Adresler" error={error} reset={reset} />;
}
