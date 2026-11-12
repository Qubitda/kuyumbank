import { Outlet } from "react-router-dom";
import { PortalShell } from "@/components/layout";
import { AppErrorBoundary } from "@/components/error-boundary";

export default function PortalLayout() {
  return (
    <PortalShell>
      <AppErrorBoundary label="Portal ekranı">
        <Outlet />
      </AppErrorBoundary>
    </PortalShell>
  );
}
