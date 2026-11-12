"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth";
import { dashboardService } from "../services";
import type {
  DashboardFilters,
  DashboardSnapshot,
  DatePreset,
} from "../types";
import { formatMoney, formatDateTime } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  RefreshCw,
  AlertCircle,
  ShoppingCart,
  Package,
  Building2,
  Gem,
  Boxes,
  Receipt,
  Truck,
  FileText,
  Tag,
  Bell,
  ArrowRight,
  Wallet,
  Briefcase,
} from "lucide-react";
import type { Capabilities } from "@/lib/api/types";

function todayLabel(d = new Date()): string {
  return new Intl.DateTimeFormat("tr-TR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Europe/Istanbul",
  }).format(d);
}

function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function rangeFromPreset(preset: DatePreset): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  if (preset === "7d") from.setDate(to.getDate() - 7);
  else if (preset === "30d") from.setDate(to.getDate() - 30);
  else if (preset === "90d") from.setDate(to.getDate() - 90);
  return { from: toIsoDate(from), to: toIsoDate(to) };
}

function greeting(hour: number): string {
  if (hour < 12) return "Günaydın";
  if (hour < 18) return "İyi günler";
  return "İyi akşamlar";
}

function emptySnap(): DashboardSnapshot {
  return {
    meDashboard: null,
    orders: [],
    ordersCount: null,
    approvals: [],
    approvalsCount: null,
    cari: [],
    credit: null,
    ledger: [],
    stock: [],
    stockCount: null,
    shipments: [],
    shipmentsCount: null,
    catalogCount: null,
    commercialReport: null,
    behaviorReport: null,
    opsSummary: null,
    errors: {},
  };
}

type Kpi = {
  key: string;
  label: string;
  value: string;
  href: string;
  hint?: string;
  loading?: boolean;
  empty?: boolean;
};

export function HomeDashboardView() {
  const { user } = useAuth();
  const caps = user?.capabilities;

  const initialRange = rangeFromPreset("30d");
  const [filters, setFilters] = useState<DashboardFilters>({
    datePreset: "30d",
    dateFrom: initialRange.from,
    dateTo: initialRange.to,
    orderDurum: "all",
  });
  const [snap, setSnap] = useState<DashboardSnapshot>(emptySnap);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (mode: "full" | "soft" = "full") => {
      if (mode === "full") setLoading(true);
      else setRefreshing(true);
      setError(null);
      try {
        const next = await dashboardService.loadSnapshot(caps, filters);
        setSnap(next);
        if (!next.meDashboard && next.errors.meDashboard) {
          setError(next.errors.meDashboard);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Dashboard yüklenemedi.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [caps, filters]
  );

  useEffect(() => {
    void load("full");
  }, [load]);

  const setPreset = (preset: DatePreset) => {
    if (preset === "custom") {
      setFilters((f) => ({ ...f, datePreset: "custom" }));
      return;
    }
    const r = rangeFromPreset(preset);
    setFilters((f) => ({
      ...f,
      datePreset: preset,
      dateFrom: r.from,
      dateTo: r.to,
    }));
  };

  const filteredOrders = useMemo(() => {
    if (filters.orderDurum === "all") return snap.orders;
    return snap.orders.filter((o) => o.durum === filters.orderDurum);
  }, [snap.orders, filters.orderDurum]);

  const statusDist = useMemo(() => {
    const map = new Map<string, number>();
    for (const o of snap.orders) {
      map.set(o.durum, (map.get(o.durum) || 0) + 1);
    }
    const total = snap.orders.length || 1;
    return [...map.entries()]
      .map(([durum, count]) => ({
        durum,
        count,
        pct: Math.round((count / total) * 100),
      }))
      .sort((a, b) => b.count - a.count);
  }, [snap.orders]);

  const pendingApprovals = useMemo(
    () => snap.approvals.filter((a) => a.durum === "BEKLEMEDE"),
    [snap.approvals]
  );
  const pendingOrders = useMemo(
    () => snap.orders.filter((o) => o.durum === "BEKLEMEDE"),
    [snap.orders]
  );
  const delivered = useMemo(
    () =>
      snap.shipments.filter(
        (s) => s.durum === "TESLIM_EDILDI" || s.durum === "TAMAMLANDI"
      ).length,
    [snap.shipments]
  );

  const cariNet = useMemo(() => {
    let alacak = 0;
    let borc = 0;
    for (const c of snap.cari) {
      const n = Number(c.bakiye);
      if (!Number.isFinite(n)) continue;
      if (n > 0) alacak += n;
      else if (n < 0) borc += Math.abs(n);
    }
    return { alacak, borc, currency: snap.cari[0]?.para_birimi || "TRY" };
  }, [snap.cari]);

  const stockAvailableSum = useMemo(() => {
    let sum = 0;
    let has = false;
    for (const s of snap.stock) {
      const n = Number(s.available);
      if (Number.isFinite(n)) {
        sum += n;
        has = true;
      }
    }
    return has ? sum : null;
  }, [snap.stock]);

  const kpis = useMemo((): Kpi[] => {
    const list: Kpi[] = [];
    const dash = snap.meDashboard;

    if (dash) {
      list.push({
        key: "orders",
        label: "Toplam sipariş",
        value:
          dash.order_count != null
            ? String(dash.order_count)
            : snap.ordersCount != null
              ? String(snap.ordersCount)
              : "—",
        href: "/siparis",
        empty: dash.order_count == null && snap.ordersCount == null,
      });
      list.push({
        key: "cart",
        label: "Sepet kalemi",
        value:
          dash.cart_line_count != null ? String(dash.cart_line_count) : "—",
        href: "/siparis",
        empty: dash.cart_line_count == null,
      });
      list.push({
        key: "rfq",
        label: "RFQ",
        value: dash.rfq_count != null ? String(dash.rfq_count) : "—",
        href: "/teklifler",
        empty: dash.rfq_count == null,
        hint:
          dash.rfq_ozel_count != null
            ? `${dash.rfq_ozel_count} özel RFQ`
            : undefined,
      });
    } else if (loading) {
      list.push({
        key: "orders-loading",
        label: "Toplam sipariş",
        value: "…",
        href: "/siparis",
        loading: true,
      });
    }

    if (caps?.can_view_orders && pendingOrders.length >= 0 && snap.orders.length) {
      list.push({
        key: "pending-orders",
        label: "Bekleyen sipariş",
        value: String(pendingOrders.length),
        href: "/siparis",
        hint: "Yüklenen son siparişler içinde",
      });
    }

    if (caps?.can_approve) {
      list.push({
        key: "approvals",
        label: "Onay bekleyen",
        value:
          snap.errors.approvals && snap.approvalsCount == null
            ? "—"
            : String(pendingApprovals.length),
        href: "/firmalar",
        empty: Boolean(snap.errors.approvals) && snap.approvals.length === 0,
      });
    }

    if (caps?.can_view_catalog) {
      list.push({
        key: "catalog",
        label: "Katalog ürün",
        value:
          snap.catalogCount != null
            ? String(snap.catalogCount)
            : snap.errors.catalog
              ? "—"
              : loading
                ? "…"
                : "—",
        href: "/urunler",
        empty: snap.catalogCount == null,
        loading: loading && snap.catalogCount == null && !snap.errors.catalog,
      });
    }

    if (caps?.can_view_supplier_stock) {
      list.push({
        key: "stock",
        label: "Stok kalemi",
        value:
          snap.stockCount != null
            ? String(snap.stockCount)
            : snap.errors.stock
              ? "—"
              : "—",
        href: "/stok",
        hint:
          stockAvailableSum != null
            ? `Σ available ${stockAvailableSum.toLocaleString("tr-TR")}`
            : undefined,
        empty: snap.stockCount == null,
      });
    }

    if (caps?.can_view_finance && snap.cari.length) {
      list.push({
        key: "alacak",
        label: "Toplam alacak",
        value: formatMoney(cariNet.alacak, cariNet.currency),
        href: "/finans",
      });
      list.push({
        key: "borc",
        label: "Toplam borç",
        value: formatMoney(cariNet.borc, cariNet.currency),
        href: "/finans",
      });
    }

    if (caps?.can_view_credit && snap.credit) {
      list.push({
        key: "credit",
        label: "Kullanılabilir kredi",
        value:
          snap.credit.kullanilabilir != null
            ? formatMoney(snap.credit.kullanilabilir, snap.credit.para_birimi)
            : formatMoney(snap.credit.bakiye, snap.credit.para_birimi),
        href: "/finans",
      });
    }

    if ((caps?.can_view_shipments || caps?.can_manage_shipment) && snap.shipmentsCount != null) {
      list.push({
        key: "delivered",
        label: "Teslim edilen",
        value: String(delivered),
        href: "/lojistik",
        hint: `${snap.shipmentsCount} sevkiyat kaydı`,
      });
    }

    if (snap.commercialReport) {
      list.push({
        key: "ciro",
        label: "Dönem ciro (vergisiz)",
        value: formatMoney(snap.commercialReport.ciro_vergisiz, "TRY"),
        href: "/raporlar",
        hint: `${snap.commercialReport.siparis_adet} sipariş · ${filters.dateFrom} → ${filters.dateTo}`,
      });
    }

    if (caps?.can_view_ops && snap.opsSummary?.counts) {
      const entries = Object.entries(snap.opsSummary.counts).slice(0, 3);
      for (const [k, v] of entries) {
        list.push({
          key: `ops-${k}`,
          label: `Ops · ${k}`,
          value: String(v),
          href: "/raporlar",
        });
      }
    }

    return list;
  }, [
    snap,
    caps,
    loading,
    pendingOrders.length,
    pendingApprovals.length,
    stockAvailableSum,
    cariNet,
    delivered,
    filters.dateFrom,
    filters.dateTo,
  ]);

  const attention = useMemo(() => {
    const items: Array<{
      id: string;
      title: string;
      meta: string;
      href: string;
    }> = [];

    for (const a of pendingApprovals.slice(0, 5)) {
      items.push({
        id: `ap-${a.id}`,
        title: `Onay #${a.id}`,
        meta: `${formatMoney(a.tutar, a.para_birimi || "TRY")} · ${a.gerekce || "BEKLEMEDE"}`,
        href: "/firmalar",
      });
    }
    for (const o of pendingOrders.slice(0, 5)) {
      items.push({
        id: `ord-${o.id}`,
        title: `Sipariş #${o.id}`,
        meta: `${o.durum} · ${formatDateTime(o.olusturma_tarihi)}`,
        href: "/siparis",
      });
    }
    if (snap.meDashboard?.rfq_count && snap.meDashboard.rfq_count > 0) {
      items.push({
        id: "rfq",
        title: "Açık RFQ kayıtları",
        meta: `${snap.meDashboard.rfq_count} RFQ`,
        href: "/teklifler",
      });
    }
    if (
      snap.credit?.limit_aktif &&
      snap.credit.kullanilabilir != null &&
      Number(snap.credit.kullanilabilir) <= 0
    ) {
      items.push({
        id: "credit-warn",
        title: "Kredi limiti dolu",
        meta: formatMoney(snap.credit.kullanilabilir, snap.credit.para_birimi),
        href: "/finans",
      });
    }
    return items;
  }, [pendingApprovals, pendingOrders, snap.meDashboard, snap.credit]);

  const quickLinks = useMemo(() => {
    const c = caps || ({} as Capabilities);
    const links: Array<{
      href: string;
      label: string;
      icon: React.ComponentType<{ className?: string }>;
      show: boolean;
    }> = [
      { href: "/siparis", label: "Sipariş / sepet", icon: ShoppingCart, show: Boolean(c.can_view_orders || c.can_view_cart || c.can_checkout) },
      { href: "/urunler", label: "Katalog", icon: Gem, show: Boolean(c.can_view_catalog) },
      { href: "/fiyatlama", label: "Fiyat / quote", icon: Tag, show: Boolean(c.can_lock_quote) },
      { href: "/teklifler", label: "Tedarikçi RFQ", icon: Briefcase, show: Boolean(c.can_manage_offers || c.can_manage_rfq) },
      { href: "/stok", label: "Stok", icon: Boxes, show: Boolean(c.can_view_supplier_stock) },
      { href: "/finans", label: "Finans", icon: Receipt, show: Boolean(c.can_view_finance || c.can_view_credit) },
      { href: "/lojistik", label: "Lojistik", icon: Truck, show: Boolean(c.can_view_shipments || c.can_manage_shipment) },
      { href: "/firmalar", label: "Firma / onay", icon: Building2, show: Boolean(c.can_manage_org || c.can_approve) },
      { href: "/belgeler", label: "Belgeler", icon: FileText, show: true },
      { href: "/raporlar", label: "Raporlar", icon: Package, show: true },
    ];
    return links.filter((l) => l.show);
  }, [caps]);

  const hour = new Date().getHours();
  const displayName =
    snap.meDashboard?.username || user?.username || "kullanıcı";
  const firmaAd =
    snap.meDashboard?.firma_ad || user?.firma?.ad || null;
  const firmaKod = snap.meDashboard?.firma_kodu || null;

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex flex-col gap-6 max-w-[1100px]">
        {/* Üst */}
        <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1.5">
            <p className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
              {todayLabel()}
            </p>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              {greeting(hour)}, {displayName}
            </h1>
            <p className="text-xs text-muted-foreground">
              {firmaAd ? (
                <>
                  <span className="text-foreground font-medium">{firmaAd}</span>
                  {firmaKod ? (
                    <span className="font-mono text-muted-foreground">
                      {" "}
                      · {firmaKod}
                    </span>
                  ) : null}
                  {user?.rol ? (
                    <span className="text-muted-foreground"> · {user.rol}</span>
                  ) : null}
                </>
              ) : (
                "Oturum firmanızın özet paneli"
              )}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 self-start"
            disabled={loading || refreshing}
            onClick={() => void load("soft")}
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${refreshing || loading ? "animate-spin" : ""}`}
            />
            Yenile
          </Button>
        </div>

        {/* Filtreler */}
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="flex flex-wrap gap-1 rounded-[6px] border border-border bg-muted/40 p-1">
            {(
              [
                ["7d", "7 gün"],
                ["30d", "30 gün"],
                ["90d", "90 gün"],
                ["custom", "Özel"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setPreset(id)}
                className={`rounded-[4px] px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  filters.datePreset === id
                    ? "bg-card text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="date"
              value={filters.dateFrom}
              onChange={(e) =>
                setFilters((f) => ({
                  ...f,
                  datePreset: "custom",
                  dateFrom: e.target.value,
                }))
              }
              className="h-9 w-[140px] text-xs"
            />
            <span className="text-xs text-muted-foreground">—</span>
            <Input
              type="date"
              value={filters.dateTo}
              onChange={(e) =>
                setFilters((f) => ({
                  ...f,
                  datePreset: "custom",
                  dateTo: e.target.value,
                }))
              }
              className="h-9 w-[140px] text-xs"
            />
          </div>
          <select
            value={filters.orderDurum}
            onChange={(e) =>
              setFilters((f) => ({ ...f, orderDurum: e.target.value }))
            }
            className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs"
            aria-label="Sipariş durumu"
          >
            <option value="all">Tüm durumlar</option>
            {[
              "TASLAK",
              "BEKLEMEDE",
              "ONAYLANDI",
              "HAZIRLANIYOR",
              "SEVKIYAT",
              "TAMAMLANDI",
              "IPTAL",
            ].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div
            className="flex items-center justify-between rounded-[8px] border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive"
            role="alert"
          >
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="h-8"
              onClick={() => void load("soft")}
            >
              Yeniden dene
            </Button>
          </div>
        )}

        {/* KPI */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-foreground">Özet göstergeler</h2>
          {kpis.length === 0 && !loading ? (
            <p className="text-xs text-muted-foreground">
              Bu oturum için gösterilecek KPI bulunamadı.
            </p>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {kpis.map((k) => (
                <Tooltip key={k.key}>
                  <TooltipTrigger asChild>
                    <Link
                      href={k.href}
                      className="rounded-[8px] border border-border bg-card p-4 space-y-1 hover:bg-muted/40 transition-colors"
                    >
                      <div className="text-[11px] text-muted-foreground">
                        {k.label}
                      </div>
                      <div
                        className={`text-xl font-semibold font-mono tabular-nums ${
                          k.empty || k.loading
                            ? "text-muted-foreground"
                            : "text-foreground"
                        }`}
                      >
                        {k.loading ? "…" : k.empty && k.value === "—" ? "Veri yok" : k.value}
                      </div>
                      {k.hint ? (
                        <div className="text-[10px] text-muted-foreground truncate">
                          {k.hint}
                        </div>
                      ) : null}
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">
                    {k.href} · {k.label}
                  </TooltipContent>
                </Tooltip>
              ))}
            </div>
          )}
        </section>

        {/* Hızlı erişim */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-foreground">Hızlı erişim</h2>
          <div className="flex flex-wrap gap-2">
            {quickLinks.map((l) => {
              const Icon = l.icon;
              return (
                <Link
                  key={l.href + l.label}
                  href={l.href}
                  className="inline-flex items-center gap-1.5 rounded-[6px] border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted/50 transition-colors"
                >
                  <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                  {l.label}
                </Link>
              );
            })}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Durum dağılımı */}
          <section className="lg:col-span-2 rounded-[8px] border border-border bg-card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground">
                Sipariş durum dağılımı
              </h2>
              <span className="text-[10px] text-muted-foreground font-mono">
                son {snap.orders.length} kayıt
              </span>
            </div>
            {!caps?.can_view_orders && !caps?.can_view_cart ? (
              <p className="text-xs text-muted-foreground">Yetkiniz yok.</p>
            ) : snap.errors.orders ? (
              <p className="text-xs text-destructive">{snap.errors.orders}</p>
            ) : loading && snap.orders.length === 0 ? (
              <p className="text-xs text-muted-foreground animate-pulse">Yükleniyor…</p>
            ) : statusDist.length === 0 ? (
              <p className="text-xs text-muted-foreground">Sipariş kaydı yok.</p>
            ) : (
              <ul className="space-y-2.5">
                {statusDist.map((row) => (
                  <li key={row.durum} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-foreground">{row.durum}</span>
                      <span className="tabular-nums text-muted-foreground">
                        {row.count} · %{row.pct}
                      </span>
                    </div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full bg-foreground/70"
                            style={{ width: `${row.pct}%` }}
                          />
                        </div>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">
                        {row.durum}: {row.count} sipariş
                      </TooltipContent>
                    </Tooltip>
                  </li>
                ))}
              </ul>
            )}
            {snap.commercialReport ? (
              <div className="border-t border-border pt-3 space-y-1 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Dönem sipariş</span>
                  <span className="font-mono tabular-nums text-foreground">
                    {snap.commercialReport.siparis_adet}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Dönem ciro</span>
                  <span className="font-mono tabular-nums text-foreground">
                    {formatMoney(snap.commercialReport.ciro_vergisiz, "TRY")}
                  </span>
                </div>
                {snap.behaviorReport?.quote_adet != null ? (
                  <div className="flex justify-between">
                    <span>Quote adedi</span>
                    <span className="font-mono tabular-nums text-foreground">
                      {snap.behaviorReport.quote_adet}
                    </span>
                  </div>
                ) : null}
              </div>
            ) : snap.errors.reports ? (
              <p className="text-[11px] text-muted-foreground border-t border-border pt-3">
                Dönem raporu yok veya yetkisiz.
              </p>
            ) : null}
            <p className="text-[10px] text-muted-foreground leading-relaxed">
              Günlük/haftalık zaman serisi endpoint’i yok; dağılım yüklü
              siparişlerden, dönem özeti `/reports/orders/` ile gelir.
            </p>
          </section>

          {/* Bildirim / dikkat */}
          <section className="lg:col-span-3 rounded-[8px] border border-border bg-card p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">
                Bekleyen işlemler
              </h2>
            </div>
            {attention.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                Dikkat gerektiren kayıt yok (veya ilgili uçlar yetkisiz).
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {attention.map((item) => (
                  <li key={item.id}>
                    <Link
                      href={item.href}
                      className="flex items-center justify-between gap-3 py-2.5 hover:bg-muted/30 -mx-1 px-1 rounded-[4px]"
                    >
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-foreground truncate">
                          {item.title}
                        </div>
                        <div className="text-[11px] text-muted-foreground truncate">
                          {item.meta}
                        </div>
                      </div>
                      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        {/* Son işlemler */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <RecentBlock
            title="Son siparişler"
            href="/siparis"
            empty={!caps?.can_view_orders && !caps?.can_view_cart}
            emptyLabel="Sipariş yetkisi yok"
            error={snap.errors.orders}
            loading={loading && snap.orders.length === 0}
            rows={filteredOrders.slice(0, 8).map((o) => ({
              id: String(o.id),
              primary: `#${o.id}`,
              secondary: formatDateTime(o.olusturma_tarihi),
              amount: `${o.line_count} kalem`,
              status: o.durum,
              href: "/siparis",
            }))}
          />

          <RecentBlock
            title="Son onaylar"
            href="/firmalar"
            empty={!caps?.can_approve}
            emptyLabel="Onay yetkisi yok"
            error={snap.errors.approvals}
            loading={loading && caps?.can_approve && snap.approvals.length === 0}
            rows={snap.approvals.slice(0, 8).map((a) => ({
              id: String(a.id),
              primary: `#${a.id}`,
              secondary: a.olusturma_tarihi
                ? formatDateTime(a.olusturma_tarihi)
                : a.gerekce || "—",
              amount: formatMoney(a.tutar, a.para_birimi || "TRY"),
              status: a.durum,
              href: "/firmalar",
            }))}
          />

          <RecentBlock
            title="Son ledger"
            href="/finans"
            empty={!caps?.can_view_finance}
            emptyLabel="Finans yetkisi yok"
            error={snap.errors.finance}
            loading={loading && caps?.can_view_finance && snap.ledger.length === 0}
            rows={snap.ledger.slice(0, 8).map((l) => ({
              id: String(l.id),
              primary: l.hareket_tipi || l.yon || `#${l.id}`,
              secondary: l.olusturma_tarihi
                ? formatDateTime(l.olusturma_tarihi)
                : "—",
              amount: formatMoney(l.tutar, l.para_birimi),
              status: l.yon || "—",
              href: "/finans",
            }))}
          />

          <RecentBlock
            title="Son sevkiyatlar"
            href="/lojistik"
            empty={!caps?.can_view_shipments && !caps?.can_manage_shipment}
            emptyLabel="Lojistik yetkisi yok"
            error={snap.errors.shipments}
            loading={
              loading &&
              Boolean(caps?.can_view_shipments || caps?.can_manage_shipment) &&
              snap.shipments.length === 0
            }
            rows={snap.shipments.slice(0, 8).map((s) => ({
              id: String(s.id),
              primary: `Sevkiyat #${s.id}`,
              secondary: s.order_id ? `Sipariş #${s.order_id}` : "—",
              amount: "—",
              status: s.durum,
              href: "/lojistik",
            }))}
          />
        </div>

        {/* Cari özet satırı */}
        {caps?.can_view_finance && snap.cari.length > 0 ? (
          <section className="rounded-[8px] border border-border bg-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <Wallet className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">Cari bakiyeler</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {snap.cari.slice(0, 6).map((c) => (
                <Link
                  key={c.id}
                  href="/finans"
                  className="flex items-center justify-between rounded-[6px] border border-border px-3 py-2 text-xs hover:bg-muted/40"
                >
                  <span className="font-mono text-muted-foreground">#{c.id}</span>
                  <span className="font-mono tabular-nums font-medium">
                    {formatMoney(c.bakiye, c.para_birimi)}
                  </span>
                </Link>
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </TooltipProvider>
  );
}

function RecentBlock({
  title,
  href,
  rows,
  empty,
  emptyLabel,
  error,
  loading,
}: {
  title: string;
  href: string;
  rows: Array<{
    id: string;
    primary: string;
    secondary: string;
    amount: string;
    status: string;
    href: string;
  }>;
  empty?: boolean;
  emptyLabel?: string;
  error?: string;
  loading?: boolean;
}) {
  return (
    <section className="rounded-[8px] border border-border bg-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        <Link
          href={href}
          className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
        >
          Tümü <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
      {empty ? (
        <p className="p-4 text-xs text-muted-foreground">{emptyLabel}</p>
      ) : error && rows.length === 0 ? (
        <p className="p-4 text-xs text-destructive">{error}</p>
      ) : loading ? (
        <p className="p-4 text-xs text-muted-foreground animate-pulse">Yükleniyor…</p>
      ) : rows.length === 0 ? (
        <p className="p-4 text-xs text-muted-foreground">Kayıt yok.</p>
      ) : (
        <ul className="divide-y divide-border">
          {rows.map((r) => (
            <li key={r.id}>
              <Link
                href={r.href}
                className="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/30 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium font-mono text-foreground">
                    {r.primary}
                  </div>
                  <div className="text-[11px] text-muted-foreground truncate">
                    {r.secondary}
                  </div>
                </div>
                <div className="text-right shrink-0 space-y-0.5">
                  <div className="text-[11px] font-mono tabular-nums text-foreground">
                    {r.amount}
                  </div>
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {r.status}
                  </Badge>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
