"use client";

import Link from "next/link";

import { useSession } from "@/features/auth/components/session-provider";

export default function AdminHomePage() {
  const { me } = useSession();
  if (!me) return null;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Admin portalı</h1>
        <p className="text-sm text-muted-foreground">
          {me.firma?.ad ?? "Platform"} · {me.rol || "rol yok"}
        </p>
      </header>
      <p className="text-sm text-muted-foreground">
        Siparişler admin yüzeyine düşer; tedarikçiye yönlendirme RFQ eşleştirme
        ile yapılır (BACKEND_MAP §6.1).
      </p>
      <ul className="flex flex-col gap-2 text-sm">
        {me.capabilities.can_view_ops ? (
          <li>
            <Link
              href="/admin/rfq-match"
              className="underline-offset-4 hover:underline"
            >
              RFQ eşleştirme
            </Link>
          </li>
        ) : null}
        {me.capabilities.can_view_orders ? (
          <li>
            <Link
              href="/admin/orders"
              className="underline-offset-4 hover:underline"
            >
              Sipariş özeti
            </Link>
          </li>
        ) : null}
      </ul>
    </div>
  );
}
