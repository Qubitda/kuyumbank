import { Suspense } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { RequireAuth } from "@/features/auth/components/require-auth";
import { SessionProvider } from "@/features/auth/components/session-provider";

export default function BuyerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <Suspense
        fallback={
          <p className="p-6 text-sm text-muted-foreground">Yükleniyor…</p>
        }
      >
        <RequireAuth portal="buyer">
          <AppShell portal="buyer">{children}</AppShell>
        </RequireAuth>
      </Suspense>
    </SessionProvider>
  );
}
