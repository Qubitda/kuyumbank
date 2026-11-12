"use client";

import React, { useEffect, useState } from "react";
import { fiyatlamaService } from "../services";
import {
  rememberLockId,
  rememberQuoteId,
  useSessionQuotesAndLocks,
} from "../hooks";
import { siparisService } from "@/features/siparis";
import { formatMoney, formatDateTime } from "@/lib/format";
import {
  QuoteCountdown,
  isQuoteExpired,
} from "@/components/commerce/quote-countdown";
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
import { Input } from "@/components/ui/input";
import { Tag, Lock, RefreshCw, AlertCircle } from "lucide-react";
import { useActionToast } from "@/hooks/use-action-toast";
import { mapCommerceError } from "@/lib/api/commerce-errors";
import { BlindPoolCallout } from "./blind-pool-callout";
import { BuyerNetPriceCard } from "./buyer-net-price-card";

function lockBadgeVariant(
  durum: string,
  gecerli?: boolean
): "success" | "destructive" | "warning" | "outline" {
  if (gecerli === false || /SURESI_DOLDU|IPTAL|EXPIRED/i.test(durum)) {
    return "destructive";
  }
  if (/AKTIF|ACTIVE/i.test(durum)) return "success";
  if (/KULLANILDI|USED/i.test(durum)) return "warning";
  return "outline";
}

export function PricingQuotesView() {
  const actionToast = useActionToast();
  const { quotes, locks, loading, error, refresh, setError } =
    useSessionQuotesAndLocks();
  const [lookupId, setLookupId] = useState("");
  const [lockingId, setLockingId] = useState<number | null>(null);
  const [refreshingId, setRefreshingId] = useState<number | null>(null);

  const fetchPricing = async () => {
    try {
      const cart = await siparisService.getMyCart();
      const quoteIds = (cart.lines || [])
        .map((l) => l.quote_id)
        .filter((id): id is number => Number.isFinite(id));
      quoteIds.forEach(rememberQuoteId);
      await refresh(quoteIds);
    } catch {
      await refresh();
    }
  };

  useEffect(() => {
    void fetchPricing();
  }, []);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = Number(lookupId);
    if (!Number.isFinite(id) || id <= 0) {
      setError("Geçerli bir quote id girin.");
      return;
    }
    try {
      const quote = await fiyatlamaService.getQuote(id);
      rememberQuoteId(quote.id);
      setLookupId("");
      await fetchPricing();
      actionToast.success("Quote yüklendi", `#${quote.id}`);
    } catch (err) {
      setError(mapCommerceError(err, "Quote bulunamadı."));
      actionToast.error("Quote bulunamadı", err);
    }
  };

  const handleRefreshQuote = async (quoteId: number) => {
    setRefreshingId(quoteId);
    setError(null);
    try {
      const quote = await fiyatlamaService.getQuote(quoteId);
      rememberQuoteId(quote.id);
      await fetchPricing();
      if (isQuoteExpired(quote.expires_at)) {
        actionToast.info(
          "Quote süresi dolmuş",
          "Katalogdan yeni fiyat alın."
        );
      } else {
        actionToast.success("Quote yenilendi", `#${quoteId}`);
      }
    } catch (err) {
      setError(mapCommerceError(err, "Quote yenilenemedi."));
      actionToast.error("Quote yenilenemedi", err);
    } finally {
      setRefreshingId(null);
    }
  };

  const handleLock = async (quoteId: number) => {
    const quote = quotes.find((q) => q.id === quoteId);
    if (quote && isQuoteExpired(quote.expires_at)) {
      setError("Quote süresi dolmuş. Önce yenileyin veya yeni fiyat alın.");
      actionToast.error("Quote süresi dolmuş", "Kilitleme yapılamaz.");
      return;
    }
    setLockingId(quoteId);
    setError(null);
    try {
      const lock = await fiyatlamaService.createPriceLock(quoteId);
      rememberLockId(lock.id);
      await fetchPricing();
      actionToast.success("Fiyat kilitlendi", `Quote #${quoteId}`);
    } catch (err) {
      setError(mapCommerceError(err, "Fiyat kilitlenemedi"));
      actionToast.error("Fiyat kilitlenemedi", err);
    } finally {
      setLockingId(null);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Fiyatlama, Quote & PriceLock
        </h1>
        <p className="text-xs text-muted-foreground">
          Liste GET yok. Sepetteki quote_id’ler ve oturumda oluşturulan kayıtlar
          gösterilir. Süre dolunca kilitleme kapanır; yenileme GET quote ile.
          Canlı borsa / global marj API yok —{" "}
          <span className="font-mono text-[10px]">BACKEND_GAPS.md</span>{" "}
          GAP-F3-01/02.
        </p>
      </div>

      <BlindPoolCallout role="buyer" />

      {quotes.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {quotes.slice(0, 3).map((q) => (
            <BuyerNetPriceCard key={`net-${q.id}`} quote={q} />
          ))}
        </div>
      ) : null}

      <form
        onSubmit={handleLookup}
        className="flex flex-col sm:flex-row gap-2 sm:items-end"
      >
        <div className="flex flex-col gap-1.5 flex-1">
          <label className="text-xs text-muted-foreground" htmlFor="quote-lookup">
            Quote id ile getir
          </label>
          <Input
            id="quote-lookup"
            value={lookupId}
            onChange={(e) => setLookupId(e.target.value)}
            inputMode="numeric"
            className="font-mono"
          />
        </div>
        <Button type="submit" size="sm" className="h-9">
          Getir
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-9"
          onClick={() => void fetchPricing()}
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Yenile
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
            onClick={() => void fetchPricing()}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      {loading ? (
        <div
          className="flex h-48 w-full items-center justify-center"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Fiyatlama kayıtları alınıyor…</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">PriceLock</h2>
            </div>
            <div className="rounded-[8px] border border-border bg-card overflow-hidden">
              {locks.length === 0 ? (
                <div className="p-6 text-center text-xs text-muted-foreground">
                  Fiyat kilidi kaydı bulunamadı.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kilit ID</TableHead>
                      <TableHead>Quote Ref</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead className="text-right">Kilitli Tutar</TableHead>
                      <TableHead>Kalan / Bitiş</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {locks.map((l) => (
                      <TableRow key={l.id}>
                        <TableCell className="font-mono text-xs font-semibold">
                          #{l.id}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          Q-{l.quote_id}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={lockBadgeVariant(l.durum, l.gecerli)}
                            className="font-mono text-[10px]"
                          >
                            {l.durum}
                            {l.gecerli === false ? " · geçersiz" : ""}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono tabular-nums font-semibold">
                          {l.kilit_fiyati
                            ? formatMoney(l.kilit_fiyati, l.para_birimi)
                            : "—"}
                        </TableCell>
                        <TableCell className="text-xs">
                          <div className="flex flex-col gap-0.5">
                            <QuoteCountdown expiresAt={l.expires_at} />
                            <span className="text-muted-foreground">
                              {l.expires_at
                                ? formatDateTime(l.expires_at)
                                : "—"}
                            </span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">PriceQuote</h2>
            </div>
            <div className="rounded-[8px] border border-border bg-card overflow-hidden">
              {quotes.length === 0 ? (
                <div className="p-6 text-center text-xs text-muted-foreground">
                  Quote kaydı bulunamadı. Katalogdan fiyat alın veya id ile
                  getirin.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Quote No</TableHead>
                      <TableHead>Ürün / SKU</TableHead>
                      <TableHead className="text-right">Tutar</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead>Kalan süre</TableHead>
                      <TableHead className="text-right">İşlem</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {quotes.map((q) => {
                      const expired = isQuoteExpired(q.expires_at);
                      return (
                        <TableRow
                          key={q.id}
                          className={expired ? "opacity-80" : undefined}
                        >
                          <TableCell className="font-mono text-xs font-medium">
                            #{q.id}
                          </TableCell>
                          <TableCell className="text-xs">
                            <div className="font-medium text-foreground">
                              {q.urun || `Varyant #${q.varyant_id}`}
                            </div>
                            <div className="font-mono text-muted-foreground">
                              {q.varyant_sku || "—"}
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-mono tabular-nums font-medium">
                            {formatMoney(
                              q.toplam_vergisiz || q.birim_fiyat,
                              q.para_birimi
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={expired ? "destructive" : "outline"}
                              className="font-mono text-[10px]"
                            >
                              {expired ? "SÜRESİ DOLDU" : q.durum || "—"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <QuoteCountdown expiresAt={q.expires_at} />
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1.5">
                              <Button
                                variant="outline"
                                size="sm"
                                disabled={refreshingId === q.id}
                                onClick={() => void handleRefreshQuote(q.id)}
                                className="h-7 text-xs gap-1"
                                aria-label={`Quote ${q.id} yenile`}
                              >
                                <RefreshCw
                                  className={`h-3 w-3 ${
                                    refreshingId === q.id ? "animate-spin" : ""
                                  }`}
                                />
                                Yenile
                              </Button>
                              <Button
                                variant="secondary"
                                size="sm"
                                disabled={lockingId === q.id || expired}
                                onClick={() => void handleLock(q.id)}
                                className="h-7 text-xs gap-1"
                              >
                                <Lock className="h-3 w-3" />
                                Kilitle
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
