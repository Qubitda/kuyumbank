import { Suspense } from "react";

import { OrdersPanel } from "@/features/siparis/components/orders-panel";

export default function BuyerOrdersPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <OrdersPanel />
    </Suspense>
  );
}
