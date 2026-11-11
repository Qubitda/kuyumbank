import { Suspense } from "react";

import { SupplierStockClient } from "./stock-client";

export default function SupplierStockPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <SupplierStockClient />
    </Suspense>
  );
}
