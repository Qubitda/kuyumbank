import { Suspense } from "react";

import { AdminRfqMatchClient } from "./rfq-match-client";

export default function AdminRfqMatchPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <AdminRfqMatchClient />
    </Suspense>
  );
}
