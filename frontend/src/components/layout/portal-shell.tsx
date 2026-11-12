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

          <main className="flex-1 overflow-y-auto p-6 md:p-8">
            <div className="w-full">{children}</div>
          </main>
        </div>
      </div>
    </RequireAuth>
  );
}
