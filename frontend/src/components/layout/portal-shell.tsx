import Link from "next/link";

import { Button } from "@/components/ui/button";

import { PortalNav } from "./portal-nav";
import { ThemeToggle } from "./theme-toggle";

/**
 * NX-SHELL — portal çerçeve.
 * Kör havuz: alıcı UI’da tedarikçi kimliği/maliyet; tedarikçi UI’da alıcı kimliği gösterme.
 * Yetki gizleme ≠ güvenlik; her yazma backend RBAC.
 */
export function PortalShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-4 border-b border-border pb-4">
        <div className="flex items-center justify-between gap-4">
          <Link
            href="/"
            className="text-lg font-semibold tracking-tight text-foreground"
          >
            Kuyumbank
          </Link>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Giriş</Link>
            </Button>
          </div>
        </div>
        <PortalNav />
        <p className="text-xs text-muted-foreground">
          Kör havuz: karşı taraf kimliği ve maliyet alanları bu yüzeyde
          gösterilmez. Yetki API’de doğrulanır.
        </p>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
