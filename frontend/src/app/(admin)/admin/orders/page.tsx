export default function AdminOrdersPage() {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-xl font-semibold tracking-tight">Siparişler</h1>
      <p className="text-sm text-muted-foreground">
        Dilim 4 — `/api/v1/orders/` (ops okuma) + `/ops/orders/summary/`.
      </p>
    </div>
  );
}
