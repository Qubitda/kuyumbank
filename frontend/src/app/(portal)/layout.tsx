import Link from "next/link";

const NAV: { href: string; label: string }[] = [
  { href: "/firmalar", label: "Firmalar" },
  { href: "/urunler", label: "Ürünler" },
  { href: "/fiyatlama", label: "Fiyatlama" },
  { href: "/stok", label: "Stok" },
  { href: "/siparis", label: "Sipariş" },
  { href: "/finans", label: "Finans" },
  { href: "/kalite", label: "Kalite" },
  { href: "/lojistik", label: "Lojistik" },
  { href: "/tanimlar", label: "Tanımlar" },
  { href: "/belgeler", label: "Belgeler" },
];

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-4 border-b border-border pb-4">
        <div className="flex items-baseline justify-between gap-4">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            Kuyumbank
          </Link>
          <Link
            href="/login"
            className="text-sm text-muted-foreground underline-offset-4 hover:underline"
          >
            Giriş
          </Link>
        </div>
        <nav aria-label="Domain" className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
