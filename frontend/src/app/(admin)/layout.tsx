import { SessionProvider } from "@/features/auth/components/session-provider";
import { RequireAuth } from "@/features/auth/components/require-auth";
import { AppShell } from "@/components/layout/app-shell";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <RequireAuth portal="admin">
        <AppShell portal="admin">{children}</AppShell>
      </RequireAuth>
    </SessionProvider>
  );
}
