"use client";

import { formatGram, formatMoney, formatDateTime } from "@/lib/format";
import { QuoteCountdown } from "@/components/commerce/quote-countdown";
import { Badge } from "@/components/ui/badge";
import type { PriceQuote } from "../types";

/**
 * Alıcı net fiyat — yalnızca BuyerQuote alanları.
 * Marj / maliyet / tedarikçi alanları buraya eklenmez.
 */
export function BuyerNetPriceCard({ quote }: { quote: PriceQuote }) {
  return (
    <div className="rounded-[8px] border border-border bg-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-muted-foreground font-mono">Quote #{quote.id}</p>
          <p className="text-sm font-semibold text-foreground">
            {quote.urun || `Varyant #${quote.varyant_id}`}
          </p>
          <p className="font-mono text-[11px] text-muted-foreground">
            {quote.varyant_sku || "—"}
          </p>
        </div>
        <Badge variant="outline" className="font-mono text-[10px]">
          {quote.durum || "NET"}
        </Badge>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
        <div>
          <dt className="text-muted-foreground">Net toplam</dt>
          <dd className="text-right font-mono tabular-nums font-semibold text-foreground">
            {formatMoney(quote.toplam_vergisiz || quote.birim_fiyat, quote.para_birimi)}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Gram başı (net)</dt>
          <dd className="text-right font-mono tabular-nums text-foreground">
            {quote.gram_basi_vergisiz
              ? formatMoney(quote.gram_basi_vergisiz, quote.para_birimi)
              : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Gram</dt>
          <dd className="text-right font-mono tabular-nums">
            {formatGram(quote.gram)}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Kalan süre</dt>
          <dd className="text-right">
            <QuoteCountdown expiresAt={quote.expires_at} />
          </dd>
        </div>
      </dl>

      {quote.expires_at ? (
        <p className="text-[11px] text-muted-foreground">
          Bitiş: {formatDateTime(quote.expires_at)}
        </p>
      ) : null}
    </div>
  );
}
