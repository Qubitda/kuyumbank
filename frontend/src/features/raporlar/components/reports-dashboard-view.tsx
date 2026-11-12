"use client";

import React, { useState, useEffect } from "react";
import { raporlarService } from "../services";
import type {
  CommercialOrderReport,
  BuyerBehaviorReport,
  RevenueAnomalyReport,
} from "../types";
import { formatMoney } from "@/lib/format";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  BarChart3,
  TrendingUp,
  ShieldAlert,
  RefreshCw,
  AlertCircle,
  Package,
  ShoppingCart,
  Calendar,
} from "lucide-react";

export function ReportsDashboardView() {
  const [activeTab, setActiveTab] = useState<"commercial" | "behavior" | "anomaly">("commercial");

  const [orderReport, setOrderReport] = useState<CommercialOrderReport | null>(null);
  const [behaviorReport, setBehaviorReport] = useState<BuyerBehaviorReport | null>(null);
  const [anomalyReport, setAnomalyReport] = useState<RevenueAnomalyReport | null>(null);

  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [esikCiro, setEsikCiro] = useState("500000");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      };

      const [commRes, behRes, anomRes] = await Promise.allSettled([
        raporlarService.getCommercialOrders(params),
        raporlarService.getBuyerBehavior(params),
        raporlarService.getRevenueAnomalies(esikCiro),
      ]);

      if (commRes.status === "fulfilled") setOrderReport(commRes.value);
      if (behRes.status === "fulfilled") setBehaviorReport(behRes.value);
      if (anomRes.status === "fulfilled") setAnomalyReport(anomRes.value);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rapor verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchReports();
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık ve Sekmeler */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Ticari Raporlar & Analitik
          </h1>
          <p className="text-xs text-muted-foreground">
            Sipariş/ciro özetleri, alıcı davranış metrikleri ve anomali risk eşik taraması (Faz 11).
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-[6px] border border-border bg-muted/40 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("commercial")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "commercial"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BarChart3 className="h-3.5 w-3.5" />
            <span>Ticari Sipariş & Ciro</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("behavior")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "behavior"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <TrendingUp className="h-3.5 w-3.5" />
            <span>Alıcı Davranış</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("anomaly")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "anomaly"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>Ciro Anomali</span>
          </button>
        </div>
      </div>

      {/* Tarih ve Eşik Filtre Formu */}
      <form
        onSubmit={handleFilterSubmit}
        className="flex flex-wrap items-end gap-3 rounded-[8px] border border-border bg-card p-4"
      >
        <div className="flex flex-col gap-1.5">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>Başlangıç Tarihi</span>
          </span>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="h-8 text-xs w-36"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>Bitiş Tarihi</span>
          </span>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="h-8 text-xs w-36"
          />
        </div>

        {activeTab === "anomaly" && (
          <div className="flex flex-col gap-1.5">
            <span className="text-xs text-muted-foreground">Eşik Ciro (TRY)</span>
            <Input
              type="text"
              value={esikCiro}
              onChange={(e) => setEsikCiro(e.target.value)}
              placeholder="500000"
              className="h-8 text-xs w-36"
            />
          </div>
        )}

        <Button type="submit" size="sm" className="h-8 text-xs">
          Raporu Güncelle
        </Button>
      </form>

      {error && (
        <div
          className="flex items-center justify-between rounded-[8px] border border-destructive/20 bg-destructive/10 p-4 text-xs text-destructive"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchReports}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      {loading ? (
        <div className="flex h-48 w-full items-center justify-center">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Rapor hesaplanıyor…</span>
          </div>
        </div>
      ) : activeTab === "commercial" ? (
        /* Ticari Sipariş & Ciro Raporu (F11-010) */
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            {!orderReport ? (
              <div className="sm:col-span-4 rounded-[8px] border border-border p-8 text-center text-xs text-muted-foreground">
                Ticari sipariş raporu verisi bulunamadı.
              </div>
            ) : (
              <>
            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">Toplam Sipariş</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {orderReport.siparis_adet}
              </p>
            </div>

            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">Oluşturulan</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {orderReport.siparis_olusturuldu ?? "—"}
              </p>
            </div>

            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">İptal Edilen</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-destructive">
                {orderReport.siparis_iptal ?? "—"}
              </p>
            </div>

            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">Vergisiz Ciro</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {formatMoney(orderReport.ciro_vergisiz, "TRY")}
              </p>
            </div>
              </>
            )}
          </div>

          <div className="rounded-[8px] border border-border bg-card p-5 space-y-2 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Hesaplama Kriteri:</span>
            <p>
              Tüm tutarlar veritabanındaki değişmez satır snapshot'larından (`snapshot_satir_tutari_vergisiz`)
              toplanarak hesaplanır. Çapraz tenant sızıntısı backend otoritesinde engellenmiştir.
            </p>
          </div>
        </div>
      ) : activeTab === "behavior" ? (
        /* Alıcı Davranış Analitiği (F11-021) */
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            {!behaviorReport ? (
              <div className="sm:col-span-4 rounded-[8px] border border-border p-8 text-center text-xs text-muted-foreground">
                Alıcı davranış raporu verisi bulunamadı.
              </div>
            ) : (
              <>
            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">Verilen Sipariş</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {behaviorReport.siparis_adet ?? "—"}
              </p>
            </div>

            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">Satır Adedi</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {behaviorReport.satir_adet ?? "—"}
              </p>
            </div>

            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">Quote Adedi</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {behaviorReport.quote_adet ?? "—"}
              </p>
            </div>

            <div className="rounded-[8px] border border-border bg-card p-5 space-y-1">
              <span className="text-xs text-muted-foreground">Vergisiz Ciro</span>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {behaviorReport.ciro_vergisiz != null
                  ? formatMoney(behaviorReport.ciro_vergisiz, "TRY")
                  : "—"}
              </p>
            </div>
              </>
            )}
          </div>

          <div className="rounded-[8px] border border-border bg-card p-5 space-y-2 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Kör Havuz Davranış Kuralı:</span>
            <p>
              Alıcı davranış metriklerinde tedarikçi isimleri ve maliyet alanları asla bulunmaz. Yalnızca
              kendi firma kesitindeki teklif alma ve satın alma dönüşüm oranları raporlanır.
            </p>
          </div>
        </div>
      ) : (
        /* Ciro Anomali Eşik Taraması (F11-014) */
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          <div className="border-b border-border px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-warning" />
              <h2 className="text-sm font-semibold text-foreground">
                {formatMoney(esikCiro, "TRY")} Üzeri Şüpheli / Yüksek Ciro Siparişleri
              </h2>
            </div>
            <Badge variant="outline" className="font-mono text-xs">
              {anomalyReport?.uyari_adet ?? 0} uyarı
            </Badge>
          </div>

          {!anomalyReport ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Anomali raporu verisi bulunamadı.
            </div>
          ) : anomalyReport.uyarilar.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Eşik ({formatMoney(anomalyReport.esik_ciro, "TRY")}) üzerinde uyarı yok.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[120px]">Sipariş No</TableHead>
                  <TableHead>Firma No</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">Sipariş Cirosu</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {anomalyReport.uyarilar.map((item, idx) => (
                  <TableRow key={String(item.id ?? idx)}>
                    <TableCell className="font-mono text-xs font-semibold">
                      {item.id != null ? `#${item.id}` : "—"}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {item.alici_firma_id != null ? `Firma #${item.alici_firma_id}` : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px]">
                        {item.durum || "—"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono tabular-nums font-semibold text-foreground">
                      {item.ciro != null ? formatMoney(String(item.ciro), "TRY") : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      )}
    </div>
  );
}
