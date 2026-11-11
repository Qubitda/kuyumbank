"use client";

import React, { useState, useEffect } from "react";
import { fiyatlamaService } from "../services";
import type { PriceQuote, PriceLock } from "../types";
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
import { Tag, Lock, RefreshCw, AlertCircle } from "lucide-react";

export function PricingQuotesView() {
  const [quotes, setQuotes] = useState<PriceQuote[]>([]);
  const [locks, setLocks] = useState<PriceLock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPricing = async () => {
    setLoading(true);
    setError(null);
    try {
      const [quoteRes, lockRes] = await Promise.allSettled([
        fiyatlamaService.getQuotes(),
        fiyatlamaService.getPriceLocks(),
      ]);

      if (quoteRes.status === "fulfilled") setQuotes(quoteRes.value || []);
      if (lockRes.status === "fulfilled") setLocks(lockRes.value || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fiyatlama verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPricing();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık Alanı */}
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Fiyatlama, Quote & PriceLock
        </h1>
        <p className="text-xs text-muted-foreground">
          Dinamik kur fiyatlaması, TTL süre kısıtlı PriceQuote ve kilitlenmiş PriceLock kayıtları.
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
            onClick={fetchPricing}
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
            <span>Fiyatlama kayıtları alınıyor…</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          {/* Fiyat Kilitleri (PriceLocks) */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">
                Aktif ve Geçmiş Fiyat Kilitleri (PriceLock)
              </h2>
            </div>

            <div className="rounded-[8px] border border-border bg-card overflow-hidden">
              {locks.length === 0 ? (
                <div className="p-6 text-center text-xs text-muted-foreground">
                  Tanımlı fiyat kilidi kaydı bulunmamaktadır.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kilit ID</TableHead>
                      <TableHead>Quote Ref</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead className="text-right">Kilitli Fiyat</TableHead>
                      <TableHead>Geçerlilik Bitiş</TableHead>
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
                            variant={l.durum === "AKTIF" ? "success" : "outline"}
                            className="font-mono text-[10px]"
                          >
                            {l.durum}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono tabular-nums font-semibold text-foreground">
                          {formatMoney(l.kilit_fiyati, l.para_birimi)}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {formatDateTime(l.expires_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </div>

          {/* Fiyat Teklifleri (PriceQuotes) */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">
                Sunulan Fiyat Teklifleri (PriceQuote)
              </h2>
            </div>

            <div className="rounded-[8px] border border-border bg-card overflow-hidden">
              {quotes.length === 0 ? (
                <div className="p-6 text-center text-xs text-muted-foreground">
                  Aktif fiyat teklifi kaydı bulunmamaktadır.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Quote No</TableHead>
                      <TableHead>Varyant</TableHead>
                      <TableHead className="text-right">Birim Fiyat</TableHead>
                      <TableHead>TTL (sn)</TableHead>
                      <TableHead>Geçerlilik Sonu</TableHead>
                      <TableHead className="text-right">İşlem</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {quotes.map((q) => (
                      <TableRow key={q.id}>
                        <TableCell className="font-mono text-xs font-medium">
                          #{q.id}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          Varyant #{q.varyant_id}
                        </TableCell>
                        <TableCell className="text-right font-mono tabular-nums font-medium text-foreground">
                          {formatMoney(q.birim_fiyat, q.para_birimi)}
                        </TableCell>
                        <TableCell className="font-mono text-xs tabular-nums text-muted-foreground">
                          {q.ttl_saniye ? `${q.ttl_saniye}s` : "—"}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {q.expires_at ? formatDateTime(q.expires_at) : "Süresiz"}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={async () => {
                              try {
                                await fiyatlamaService.createPriceLock(q.id);
                                await fetchPricing();
                              } catch (err) {
                                setError(err instanceof Error ? err.message : "Fiyat kilitlenemedi");
                              }
                            }}
                            className="h-7 text-xs gap-1"
                          >
                            <Lock className="h-3 w-3" />
                            <span>Kilitle (PriceLock)</span>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
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
