"use client";

import React from "react";
import {
  useCariListQuery,
  useCreditQuery,
  useFinanceMeQuery,
  useLedgerQuery,
  useOpsFinanceQuery,
} from "../hooks";
import { useAuth } from "@/features/auth/hooks/use-auth";
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
import {
  Wallet,
  CreditCard,
  RefreshCw,
  AlertCircle,
  BookOpen,
} from "lucide-react";

export function FinanceDashboardView() {
  const { user } = useAuth();
  const canOpsFinance = Boolean(user?.capabilities?.can_view_ops_finance);

  const meQ = useFinanceMeQuery("TRY");
  const creditQ = useCreditQuery("TRY");
  const cariQ = useCariListQuery();
  const ledgerQ = useLedgerQuery();
  const opsQ = useOpsFinanceQuery(canOpsFinance);

  const loading =
    meQ.isLoading || creditQ.isLoading || cariQ.isLoading || ledgerQ.isLoading;
  const credit = creditQ.data ?? null;
  const cariList = cariQ.data ?? [];
  const ledger = ledgerQ.data ?? [];
  const hasAnyData = Boolean(
    credit || cariList.length || ledger.length || meQ.data
  );

  const errorMsg =
    [creditQ, cariQ, ledgerQ].every((q) => q.isError) && !hasAnyData
      ? "Finansal veriler alınamadı."
      : null;

  const refetchAll = () => {
    void meQ.refetch();
    void creditQ.refetch();
    void cariQ.refetch();
    void ledgerQ.refetch();
    if (canOpsFinance) void opsQ.refetch();
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 border-b border-border pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Finans & Cari Hesaplar
          </h1>
          <p className="text-xs text-muted-foreground">
            Cari bakiye, kredi limiti ve ledger — yalnız backend yanıtı (kör
            havuz: karşı firma yok).
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refetchAll}
          className="gap-1.5"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Yenile
        </Button>
      </div>

      {meQ.data?.server_now && (
        <p className="text-[11px] text-muted-foreground font-mono">
          server_now: {formatDateTime(meQ.data.server_now)}
          {meQ.data.para_birimi ? ` · ${meQ.data.para_birimi}` : ""}
        </p>
      )}

      {errorMsg && (
        <div
          className="flex items-center justify-between rounded-[8px] border border-destructive/20 bg-destructive/10 p-4 text-xs text-destructive"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={refetchAll}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      {canOpsFinance && opsQ.data && (
        <div className="rounded-[8px] border border-border bg-muted/30 px-4 py-3 text-xs">
          <p className="font-medium text-foreground mb-1">Ops finans özeti</p>
          <p className="font-mono tabular-nums text-muted-foreground">
            cari={opsQ.data.cari_count} · ledger={opsQ.data.ledger_count} ·
            payment_intent={opsQ.data.payment_intent_count}
          </p>
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
          <span className="text-sm font-medium text-foreground">
            Veri bulunamadı
          </span>
          <span className="max-w-sm">
            Cari, kredi veya ledger kaydı dönmedi. Yetki veya hesap tanımlarını
            kontrol edin.
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
                    <span className="font-mono tabular-nums text-foreground">
                      {formatMoney(credit.bakiye, credit.para_birimi)}
                    </span>
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Kullanılabilir:{" "}
                    <span className="font-mono tabular-nums text-foreground">
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
                <p className="text-sm text-muted-foreground">
                  Kredi verisi bulunamadı.
                </p>
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
              <h2 className="text-sm font-semibold text-foreground">
                Cari Hesap Dökümü
              </h2>
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
                      <TableCell className="font-mono text-xs">
                        {c.para_birimi}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {c.guncelleme_tarihi
                          ? formatDateTime(c.guncelleme_tarihi)
                          : "—"}
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
                      <TableCell className="font-mono text-xs">
                        #{row.id}
                      </TableCell>
                      <TableCell className="font-mono text-[11px]">
                        {[row.yon, row.hareket_tipi].filter(Boolean).join(" · ") ||
                          "—"}
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
