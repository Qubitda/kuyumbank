"use client";

import React, { useState, useEffect } from "react";
import { finansService } from "../services";
import type { CariHesap, CreditInfo } from "../types";
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
import { Badge } from "@/components/ui/badge";
import { Wallet, CreditCard, RefreshCw, AlertCircle, ArrowUpRight } from "lucide-react";

export function FinanceDashboardView() {
  const [cari, setCari] = useState<CariHesap | null>(null);
  const [credit, setCredit] = useState<CreditInfo | null>(null);
  const [cariList, setCariList] = useState<CariHesap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFinanceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [myCari, myCredit, allCari] = await Promise.allSettled([
        finansService.getMyFinance(),
        finansService.getMyCredit(),
        finansService.getCariList(),
      ]);

      if (myCari.status === "fulfilled") setCari(myCari.value);
      if (myCredit.status === "fulfilled") setCredit(myCredit.value);
      if (allCari.status === "fulfilled") setCariList(allCari.value || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Finansal veriler alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinanceData();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık Alanı */}
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Finans & Cari Hesaplar
        </h1>
        <p className="text-xs text-muted-foreground">
          Cari bakiye durumu, kredi limitleri ve çift taraflı defter (Ledger) takibi.
        </p>
      </div>

      {/* Hata Bildirimi */}
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
            onClick={fetchFinanceData}
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
            <span>Finansal veriler yükleniyor…</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Özet Kartları */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Cari Bakiye */}
            <div className="rounded-[8px] border border-border bg-card p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="font-medium">Cari Hesap Bakiyesi</span>
                <Wallet className="h-4 w-4" />
              </div>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {formatMoney(cari?.bakiye ?? "0.00", cari?.para_birimi || "TRY")}
              </p>
              <p className="text-[11px] text-muted-foreground">
                Has Altın Karşılığı:{" "}
                <span className="font-mono text-foreground font-medium">
                  {cari?.has_bakiye ? `${cari.has_bakiye} g` : "—"}
                </span>
              </p>
            </div>

            {/* Kredi Limiti */}
            <div className="rounded-[8px] border border-border bg-card p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="font-medium">Tahsis Edilen Kredi</span>
                <CreditCard className="h-4 w-4" />
              </div>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {formatMoney(credit?.kredi_limiti ?? "0.00", "TRY")}
              </p>
              <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                <span>Durum:</span>
                <Badge variant="outline" className="font-mono text-[10px]">
                  {credit?.durum || "AKTIF"}
                </Badge>
              </div>
            </div>

            {/* Kalan Kredi Limiti */}
            <div className="rounded-[8px] border border-border bg-card p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="font-medium">Kullanılabilir Limit</span>
                <ArrowUpRight className="h-4 w-4" />
              </div>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {formatMoney(credit?.kalan_limit ?? "0.00", "TRY")}
              </p>
              <p className="text-[11px] text-muted-foreground">
                Kullanılan: {formatMoney(credit?.kullanilan_limit ?? "0.00", "TRY")}
              </p>
            </div>
          </div>

          {/* Cari Hesaplar Tablosu */}
          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold text-foreground">
                Cari Hesap ve Bakiye Dökümü
              </h2>
            </div>
            {cariList.length === 0 && !cari ? (
              <div className="flex h-36 flex-col items-center justify-center gap-1 text-center p-6 text-xs text-muted-foreground">
                <Wallet className="h-6 w-6 opacity-40 mb-1" />
                <span>Kayıtlı cari hesap verisi bulunamadı.</span>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Firma / Hesap</TableHead>
                    <TableHead>Para Birimi</TableHead>
                    <TableHead className="text-right">Has Bakiye</TableHead>
                    <TableHead className="text-right">Cari Bakiye</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(cariList.length > 0 ? cariList : cari ? [cari] : []).map((c) => (
                    <TableRow key={c.id}>
                      <TableCell className="font-mono text-xs font-medium">
                        Firma #{c.firma_id}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {c.para_birimi}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {c.has_bakiye ? `${c.has_bakiye} g` : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums font-semibold">
                        {formatMoney(c.bakiye, c.para_birimi)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
