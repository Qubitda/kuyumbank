import Link from "next/link";
import { Suspense } from "react";

import { SessionPanel } from "@/features/auth";

const DOMAINS = [
  "/firmalar",
  "/urunler",
  "/fiyatlama",
  "/stok",
  "/siparis",
  "/finans",
  "/kalite",
  "/lojistik",
  "/tanimlar",
  "/belgeler",
] as const;

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-10 px-6 py-16">
      <header className="flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">NX-FE · feature mimari</p>
        <h1 className="text-2xl font-semibold tracking-tight">Kuyumbank</h1>
        <p className="max-w-prose text-sm text-muted-foreground">
          Session + CSRF ile <code className="font-mono text-xs">/api/v1/</code>{" "}
          (aynı-origin rewrite). Domain iskeleti:{" "}
          <code className="font-mono text-xs">features/*</code> ↔ Django apps.
        </p>
      </header>
      <Suspense
        fallback={
          <p className="text-sm text-muted-foreground">Oturum kontrol ediliyor…</p>
        }
      >
        <SessionPanel />
      </Suspense>
      <section className="flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">Portal domain route’ları</p>
        <ul className="flex flex-wrap gap-2">
          {DOMAINS.map((href) => (
            <li key={href}>
              <Link
                href={href}
                className="inline-flex rounded-md border border-border px-2 py-1 font-mono text-xs hover:bg-muted"
              >
                {href}
              </Link>
            </li>
          ))}
        </ul>
      </section>
      <footer className="border-t border-border pt-6 text-xs text-muted-foreground">
        <Link href="/login" className="hover:underline">
          /login
        </Link>
        {" · "}
        <code className="font-mono">docs/FRONTEND_ARCHITECTURE.md</code>
      </footer>
    </div>
  );
}
