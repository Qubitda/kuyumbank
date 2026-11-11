import { Suspense } from "react";

import { AdminUsersClient } from "./users-client";

export default function AdminUsersPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <AdminUsersClient />
    </Suspense>
  );
}
