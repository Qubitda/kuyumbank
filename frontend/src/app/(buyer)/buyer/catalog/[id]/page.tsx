import Link from "next/link";
import { Suspense } from "react";

import { CatalogProductClient } from "./product-client";

type Props = { params: Promise<{ id: string }> };

export default async function BuyerCatalogDetailPage({ params }: Props) {
  const { id } = await params;
  const productId = Number(id);
  if (!Number.isFinite(productId) || productId <= 0) {
    return (
      <p className="text-sm text-destructive" role="alert">
        Geçersiz ürün.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Link
        href="/buyer/catalog"
        className="w-fit text-sm text-muted-foreground underline-offset-4 hover:underline"
      >
        ← Katalog
      </Link>
      <Suspense
        fallback={
          <p className="text-sm text-muted-foreground">Ürün yükleniyor…</p>
        }
      >
        <CatalogProductClient productId={productId} />
      </Suspense>
    </div>
  );
}
