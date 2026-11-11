export default function AdminOffersPage() {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-xl font-semibold tracking-tight">Tedarikçi teklifleri</h1>
      <p className="text-sm text-muted-foreground">
        Admin tüm tedarikçi kayıtlarını görebilir — `/supplier/offers/?tedarikci_id=`.
      </p>
    </div>
  );
}
