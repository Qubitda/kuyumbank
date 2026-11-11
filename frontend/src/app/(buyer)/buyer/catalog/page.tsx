import { CatalogList } from "@/features/urunler";

export default function BuyerCatalogPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Katalog</h1>
        <p className="text-sm text-muted-foreground">
          Yayınlı ürünler · tedarikçi kimliği yok.
        </p>
      </header>
      <CatalogList />
    </div>
  );
}
