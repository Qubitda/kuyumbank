import { SessionProvider } from "@/features/auth/components/session-provider";
import { RequireAuth } from "@/features/auth/components/require-auth";
import { AppShell } from "@/components/layout/app-shell";

export default function BuyerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <RequireAuth portal="buyer">
        <AppShell portal="buyer">{children}</AppShell>
      </RequireAuth>
    </SessionProvider>
  );
}
