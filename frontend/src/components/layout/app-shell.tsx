"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";

import { Button } from "@/components/ui/button";
import { useSession } from "@/features/auth/components/session-provider";
import { filterNav, navForPortal } from "@/lib/auth/nav";
import { portalHome, type PortalKind } from "@/lib/auth/portal";
import { cn } from "@/lib/utils";

import { ThemeToggle } from "./theme-toggle";

const PORTAL_LABEL: Record<PortalKind, string> = {
  buyer: "Müşteri",
  supplier: "Tedarikçi",
  admin: "Admin",
};

export function AppShell({
  portal,
  children,
}: {
  portal: PortalKind;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { me, logout } = useSession();
  const [pending, startTransition] = useTransition();

  const caps = me?.capabilities;
  const items = caps ? filterNav(navForPortal(portal), caps) : [];

  function onLogout() {
    startTransition(async () => {
      await logout();
      router.replace("/login");
      router.refresh();
    });
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-4 border-b border-border pb-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-baseline gap-3">
            <Link
              href={portalHome(portal)}
              className="text-lg font-semibold tracking-tight text-foreground"
            >
              Kuyumbank
            </Link>
            <span className="text-xs text-muted-foreground">
              {PORTAL_LABEL[portal]}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            {me ? (
              <>
                <span className="hidden px-2 font-mono text-xs text-muted-foreground sm:inline">
                  {me.username}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={pending}
                  onClick={onLogout}
                >
                  {pending ? "…" : "Çıkış"}
                </Button>
              </>
            ) : (
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">Giriş</Link>
              </Button>
            )}
          </div>
        </div>
        <nav aria-label="Portal" className="flex flex-wrap gap-x-1 gap-y-1 text-sm">
          {items.map((item) => {
            const home = portalHome(portal);
            const active =
              pathname === item.href ||
              (item.href !== home && pathname.startsWith(`${item.href}/`));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md px-2.5 py-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
                  active && "bg-accent font-medium text-foreground",
                )}
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        {portal === "buyer" ? (
          <p className="text-xs text-muted-foreground">
            Kör havuz: tedarikçi kimliği ve maliyet bu yüzeyde gösterilmez.
          </p>
        ) : null}
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
