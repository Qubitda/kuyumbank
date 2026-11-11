import { SessionProvider } from "@/features/auth/components/session-provider";
import { RequireAuth } from "@/features/auth/components/require-auth";
import { AppShell } from "@/components/layout/app-shell";

export default function SupplierLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <RequireAuth portal="supplier">
        <AppShell portal="supplier">{children}</AppShell>
      </RequireAuth>
    </SessionProvider>
  );
}
