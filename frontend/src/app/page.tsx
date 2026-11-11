import Link from "next/link";
import { Suspense } from "react";
import { SessionPanel, DashboardCounters } from "@/features/auth";
import { DOMAIN_NAV_ITEMS } from "@/components/layout";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-8 max-w-[860px]">
      {/* Başlık Alanı */}
      <div className="flex flex-col gap-2 border-b border-border pb-6">
        <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
          Next.js Frontend · Domain Paralel Mimari
        </span>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Kuyumbank Platformu
        </h1>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Django modular monolith ile birebir paralel Next.js App Router arayüzü.
          Veri, fiyat, milyem ve yetkilendirmede tek yetkili backend otoritesidir.
        </p>
      </div>

      {/* Alıcı Dashboard Sayaçları (GET /me/dashboard/) */}
      <Suspense fallback={null}>
        <DashboardCounters />
      </Suspense>

      {/* Oturum & Yetki Durumu */}
      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          Kullanıcı Oturumu & Yetki Matrisi
        </h2>
        <Suspense
          fallback={
            <div className="rounded-[8px] border border-border bg-card p-6">
              <p className="text-sm text-muted-foreground animate-pulse">
                Oturum durumu sorgulanıyor…
              </p>
            </div>
          }
        >
          <SessionPanel />
        </Suspense>
      </section>

      {/* Domain Modülleri Grid */}
      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold tracking-tight text-foreground">
          Portal Domain Modülleri (10 Modül)
        </h2>
        <p className="text-xs text-muted-foreground">
          Her domain modülü <code className="font-mono">src/features/&lt;domain&gt;</code> altında
          izole edilmiş ve OpenAPI sözleşmesine bağlanmıştır:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {DOMAIN_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="group flex items-start gap-3 rounded-[8px] border border-border bg-card p-4 transition-colors duration-150 hover:bg-muted/50"
              >
                <div className="rounded-[4px] bg-muted p-2 text-foreground group-hover:bg-background transition-colors duration-150">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex flex-col gap-0.5 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground group-hover:underline underline-offset-2">
                      {item.label}
                    </span>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      /{item.backendApp}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    İş ekranı ve API bağlantısı aktif
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Alt Bilgi */}
      <footer className="border-t border-border pt-6 text-xs text-muted-foreground flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <span>Kör Havuz: Alıcı ↔ Tedarikçi maliyet ve kimlik gizliliği esastır.</span>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-foreground hover:underline">
            /login
          </Link>
          <span className="text-border">|</span>
          <span className="font-mono text-[11px]">tr-TR (TRY)</span>
        </div>
      </footer>
    </div>
  );
}
