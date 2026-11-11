import { Suspense } from "react";

import { SupplierOffersPanel } from "@/features/fiyatlama/components/supplier-offers-panel";

export default function SupplierOffersPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <SupplierOffersPanel />
    </Suspense>
  );
}
