"use client";

import Link from "next/link";

import { useSession } from "@/features/auth/components/session-provider";

export default function SupplierHomePage() {
  const { me } = useSession();
  if (!me) return null;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Tedarikçi portalı</h1>
        <p className="text-sm text-muted-foreground">
          {me.firma?.ad ?? "Firma"} · {me.rol || "rol yok"}
        </p>
      </header>
      <ul className="flex flex-col gap-2 text-sm">
        {me.capabilities.can_manage_offers ? (
          <li>
            <Link
              href="/supplier/offers"
              className="underline-offset-4 hover:underline"
            >
              Teklifler
            </Link>
          </li>
        ) : null}
        {me.capabilities.can_view_supplier_stock ? (
          <li>
            <Link
              href="/supplier/stock"
              className="underline-offset-4 hover:underline"
            >
              Stok
            </Link>
          </li>
        ) : null}
      </ul>
    </div>
  );
}
