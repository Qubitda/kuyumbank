"use client";

import React, { useState } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { RequireAuth, useAuth } from "@/features/auth";

export function PortalShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <RequireAuth>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <a
          href="#portal-main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[110] focus:rounded-[6px] focus:bg-card focus:px-3 focus:py-2 focus:text-xs focus:shadow-sm"
        >
          İçeriğe atla
        </a>
        <Sidebar
          capabilities={user?.capabilities}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed(!collapsed)}
        />

        <div className="flex flex-1 flex-col overflow-hidden min-w-0">
          <Header
            user={user}
            onLogout={() => {
              void logout();
            }}
          />

          <main
            id="portal-main"
            tabIndex={-1}
            className="flex-1 overflow-y-auto p-6 md:p-8 outline-none"
          >
            <div className="w-full">{children}</div>
          </main>
        </div>
      </div>
    </RequireAuth>
  );
}
