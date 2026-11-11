import { Suspense } from "react";

import { SupplierOffersPanel } from "@/features/fiyatlama/components/supplier-offers-panel";

/** Admin: aynı teklif yüzeyi (ops view_all ile tüm tedarikçiler). */
export default function AdminOffersPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <SupplierOffersPanel />
    </Suspense>
  );
}
