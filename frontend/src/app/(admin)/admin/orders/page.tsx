import { Suspense } from "react";

import { AdminOrdersClient } from "./orders-client";

export default function AdminOrdersPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <AdminOrdersClient />
    </Suspense>
  );
}
