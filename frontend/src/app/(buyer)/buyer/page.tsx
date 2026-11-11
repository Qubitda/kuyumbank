"use client";

import Link from "next/link";

import { useSession } from "@/features/auth/components/session-provider";

export default function BuyerHomePage() {
  const { me } = useSession();
  if (!me) return null;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Müşteri portalı</h1>
        <p className="text-sm text-muted-foreground">
          {me.firma?.ad ?? "Firma"} · {me.rol || "rol yok"}
        </p>
      </header>
      <ul className="flex flex-col gap-2 text-sm">
        {me.capabilities.can_view_catalog ? (
          <li>
            <Link href="/buyer/catalog" className="underline-offset-4 hover:underline">
              Katalog
            </Link>
          </li>
        ) : null}
        {me.capabilities.can_view_orders ? (
          <li>
            <Link href="/buyer/orders" className="underline-offset-4 hover:underline">
              Siparişler
            </Link>
          </li>
        ) : null}
        {me.capabilities.can_manage_rfq ? (
          <li>
            <Link href="/buyer/rfqs" className="underline-offset-4 hover:underline">
              Teklif talepleri (RFQ)
            </Link>
          </li>
        ) : null}
      </ul>
    </div>
  );
}
