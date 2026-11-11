"use client";

import React, { useEffect, useState, useTransition } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { fetchMe, logout } from "@/lib/api/client";
import type { MeResponse } from "@/lib/api/types";
import { useRouter } from "next/navigation";

export function PortalShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<MeResponse | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;
    fetchMe()
      .then((data) => {
        if (!cancelled) setUser(data);
      })
      .catch(() => {
        // Oturum yoksa veya 401 ise kullanıcı null kalır
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = () => {
    startTransition(async () => {
      try {
        await logout();
      } catch {
        // Oturum zaten sonlanmış olabilir
      }
      setUser(null);
      router.push("/login");
      router.refresh();
    });
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* 240px / 64px Sidebar */}
      <Sidebar
        capabilities={user?.capabilities}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
      />

      {/* Sağ Kolon: 56px Header + Full-Width Main */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <Header user={user} onLogout={handleLogout} />

        {/* Ana İçerik: Tabloyu max-width ile daraltmadan tam genişlik */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
