"use client";

import React, { useEffect, useState } from "react";
import { finansService } from "../services";
import type { CariHesap, CreditInfo, LedgerEntry } from "../types";
import { unwrapResults } from "@/lib/api/client";
import { formatMoney, formatDateTime } from "@/lib/format";
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
import { Wallet, CreditCard, RefreshCw, AlertCircle, BookOpen } from "lucide-react";

export function FinanceDashboardView() {
  const [credit, setCredit] = useState<CreditInfo | null>(null);
  const [cariList, setCariList] = useState<CariHesap[]>([]);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasAnyData, setHasAnyData] = useState(false);

  const fetchFinanceData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [myCredit, allCari, ledgerPage] = await Promise.allSettled([
        finansService.getMyCredit(),
        finansService.getCariList(),
        finansService.getLedger(),
      ]);

      let found = false;
      if (myCredit.status === "fulfilled") {
        setCredit(myCredit.value);
        found = true;
      } else {
        setCredit(null);
      }
      if (allCari.status === "fulfilled") {
        const rows = unwrapResults(allCari.value);
        setCariList(rows);
        if (rows.length) found = true;
      } else {
        setCariList([]);
      }
      if (ledgerPage.status === "fulfilled") {
        const rows = unwrapResults(ledgerPage.value);
        setLedger(rows);
        if (rows.length) found = true;
      } else {
        setLedger([]);
      }

      const failures = [myCredit, allCari, ledgerPage].filter(
        (r) => r.status === "rejected"
      );
      if (failures.length === 3) {
        const first = failures[0] as PromiseRejectedResult;
        setError(
          first.reason instanceof Error
            ? first.reason.message
            : "Finansal veriler alınamadı."
        );
      }
      setHasAnyData(found);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Finansal veriler alınamadı.");
      setHasAnyData(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinanceData();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Finans & Cari Hesaplar
        </h1>
        <p className="text-xs text-muted-foreground">
          Cari bakiye, kredi limiti ve ledger — yalnızca backend yanıtı.
        </p>
      </div>

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
      ) : !hasAnyData ? (
        <div className="flex h-48 flex-col items-center justify-center gap-2 text-center p-6 text-xs text-muted-foreground border border-border rounded-[8px]">
          <Wallet className="h-8 w-8 opacity-40 mb-1" />
          <span className="text-sm font-medium text-foreground">Veri bulunamadı</span>
          <span className="max-w-sm">
            Cari, kredi veya ledger kaydı dönmedi. Yetki veya hesap tanımlarını kontrol edin.
          </span>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-[8px] border border-border bg-card p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="font-medium">Kredi Özeti</span>
                <CreditCard className="h-4 w-4" />
              </div>
              {credit ? (
                <>
                  <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                    {formatMoney(credit.kredi_limiti, credit.para_birimi)}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Bakiye:{" "}
                    <span className="font-mono text-foreground">
                      {formatMoney(credit.bakiye, credit.para_birimi)}
                    </span>
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Kullanılabilir:{" "}
                    <span className="font-mono text-foreground">
                      {credit.kullanilabilir != null
                        ? formatMoney(credit.kullanilabilir, credit.para_birimi)
                        : "—"}
                    </span>
                  </p>
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {credit.limit_aktif ? "LIMIT_AKTIF" : "LIMIT_KAPALI"}
                  </Badge>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Kredi verisi bulunamadı.</p>
              )}
            </div>

            <div className="rounded-[8px] border border-border bg-card p-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="font-medium">Cari Hesaplar</span>
                <Wallet className="h-4 w-4" />
              </div>
              <p className="text-2xl font-semibold font-mono tabular-nums text-foreground">
                {cariList.length}
              </p>
              <p className="text-[11px] text-muted-foreground">
                `/finance/cari/` sonuç sayısı
              </p>
            </div>
          </div>

          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold text-foreground">Cari Hesap Dökümü</h2>
            </div>
            {cariList.length === 0 ? (
              <div className="flex h-36 flex-col items-center justify-center gap-1 text-center p-6 text-xs text-muted-foreground">
                <span>Kayıtlı cari hesap verisi bulunamadı.</span>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Hesap</TableHead>
                    <TableHead>Para Birimi</TableHead>
                    <TableHead>Güncelleme</TableHead>
                    <TableHead className="text-right">Bakiye</TableHead>
                    <TableHead className="text-right">Kredi Limiti</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cariList.map((c) => (
                    <TableRow key={c.id}>
                      <TableCell className="font-mono text-xs font-medium">
                        #{c.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{c.para_birimi}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {c.guncelleme_tarihi ? formatDateTime(c.guncelleme_tarihi) : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums font-semibold">
                        {formatMoney(c.bakiye, c.para_birimi)}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {c.kredi_limiti != null
                          ? formatMoney(c.kredi_limiti, c.para_birimi)
                          : "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>

          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            <div className="border-b border-border px-4 py-3 flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">Ledger</h2>
            </div>
            {ledger.length === 0 ? (
              <div className="flex h-36 flex-col items-center justify-center gap-1 text-center p-6 text-xs text-muted-foreground">
                <span>Ledger kaydı bulunamadı.</span>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Yön / Tip</TableHead>
                    <TableHead>Referans</TableHead>
                    <TableHead>Tarih</TableHead>
                    <TableHead className="text-right">Tutar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ledger.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="font-mono text-xs">#{row.id}</TableCell>
                      <TableCell className="font-mono text-[11px]">
                        {[row.yon, row.hareket_tipi].filter(Boolean).join(" · ") || "—"}
                      </TableCell>
                      <TableCell className="font-mono text-[11px] text-muted-foreground">
                        {row.referans_tip || "—"}
                        {row.referans_id != null ? ` #${row.referans_id}` : ""}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {row.olusturma_tarihi
                          ? formatDateTime(row.olusturma_tarihi)
                          : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums font-semibold">
                        {formatMoney(row.tutar, row.para_birimi)}
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
