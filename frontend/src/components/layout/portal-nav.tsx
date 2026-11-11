"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

export const PORTAL_NAV: { href: string; label: string }[] = [
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

export function PortalNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Domain" className="flex flex-wrap gap-x-1 gap-y-1 text-sm">
      {PORTAL_NAV.map((item) => {
        const active =
          pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-md px-2.5 py-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
              active && "bg-accent font-medium text-foreground",
            )}
            aria-current={active ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
