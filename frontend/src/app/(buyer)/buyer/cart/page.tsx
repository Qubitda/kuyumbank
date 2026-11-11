import { Suspense } from "react";

import { CartPanel } from "@/features/siparis/components/cart-panel";

export default function BuyerCartPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Yükleniyor…</p>}
    >
      <CartPanel />
    </Suspense>
  );
}
