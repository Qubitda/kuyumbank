"use client";

import { useEffect, useMemo, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { createQuote } from "@/features/fiyatlama/services";
import {
  addCartLine,
  checkout,
  createRfq,
  orderFromCheckout,
} from "@/features/siparis/services";
import {
  getCatalogItem,
  listSalesChannels,
  type SalesChannel,
} from "@/features/urunler/services";
import { ApiError } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { newIdempotencyKey } from "@/lib/utils";

type Variant = NonNullable<
  components["schemas"]["BuyerCatalogDetail"]["varyantlar"]
>[number];

type CompareRow = Variant & { urunAd: string; urunId: number; ayar?: string };

export function CatalogProductClient({ productId }: { productId: number }) {
  const [detail, setDetail] = useState<
    components["schemas"]["BuyerCatalogDetail"] | null
  >(null);
  const [channels, setChannels] = useState<SalesChannel[]>([]);
  const [channelId, setChannelId] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [compareExtra, setCompareExtra] = useState<CompareRow[]>([]);
  const [gramFilter, setGramFilter] = useState("");
  const [renkFilter, setRenkFilter] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;
    Promise.all([getCatalogItem(productId), listSalesChannels()])
      .then(([d, ch]) => {
        if (cancelled) return;
        setDetail(d);
        const list = ch.results ?? [];
        setChannels(list);
        const preferred =
          list.find((c) => c.kod === "KUYUMCU_PANEL") ||
          list.find((c) => (c.quote_ttl_saniye ?? 0) > 0) ||
          list[0];
        if (preferred) setChannelId(preferred.id);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Detay alınamadı.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [productId]);

  const variants = useMemo(() => {
    const rows = detail?.varyantlar ?? [];
    return rows.filter((v) => {
      if (gramFilter && String(v.gram ?? "") !== gramFilter) return false;
      if (renkFilter && (v.renk || "") !== renkFilter) return false;
      return true;
    });
  }, [detail, gramFilter, renkFilter]);

  const gramOptions = useMemo(() => {
    const s = new Set(
      (detail?.varyantlar ?? [])
        .map((v) => (v.gram == null ? "" : String(v.gram)))
        .filter(Boolean),
    );
    return Array.from(s).sort();
  }, [detail]);

  const renkOptions = useMemo(() => {
    const s = new Set(
      (detail?.varyantlar ?? []).map((v) => v.renk || "").filter(Boolean),
    );
    return Array.from(s).sort();
  }, [detail]);

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function addToCompare() {
    if (!detail) return;
    const picked = (detail.varyantlar ?? []).filter(
      (v) => v.id != null && selected.has(v.id),
    );
    setCompareExtra((prev) => {
      const map = new Map(prev.map((r) => [r.id!, r]));
      for (const v of picked) {
        map.set(v.id!, {
          ...v,
          urunAd: detail.ad,
          urunId: detail.id,
          ayar: detail.ayar,
        });
      }
      return Array.from(map.values());
    });
  }

  function orderVariant(varyantId: number) {
    if (!channelId) {
      setError("Satış kanalı yok — admin’den SatisKanali tanımlayın.");
      return;
    }
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        const quote = await createQuote(
          {
            varyant_id: varyantId,
            satis_kanali_id: channelId,
            para_birimi: "TRY",
          },
          newIdempotencyKey(),
        );
        await addCartLine(
          { quote_id: quote.id, miktar: "1" },
          newIdempotencyKey(),
        );
        const co = await checkout(newIdempotencyKey());
        // Runtime body: { id, durum, ... }; OpenAPI alias checkout_id olabilir.
        const checkoutId =
          (co as { checkout_id?: number; id?: number }).checkout_id ??
          (co as { id?: number }).id;
        if (co.order_id) {
          setMessage(`Sipariş oluştu #${co.order_id}`);
          return;
        }
        if (checkoutId) {
          const order = await orderFromCheckout(
            checkoutId,
            newIdempotencyKey(),
          );
          setMessage(`Sipariş oluştu #${order.id}`);
          return;
        }
        setMessage("Checkout tamamlandı; sipariş kimliği dönmedi.");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Sipariş başarısız.");
      }
    });
  }

  function rfqVariant(varyantId: number) {
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        const rfq = await createRfq(
          {
            baslik: detail?.ad ? `RFQ · ${detail.ad}` : "RFQ",
            talep_tipi: "STANDART",
            lines: [{ varyant_id: varyantId, miktar: "1", birim: "ADET" }],
          },
          newIdempotencyKey(),
        );
        setMessage(`Teklif talebi oluşturuldu #${rfq.id}`);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "RFQ başarısız.");
      }
    });
  }

  if (error && !detail) {
    return (
      <p className="text-sm text-destructive" role="alert">
        {error}
      </p>
    );
  }

  if (!detail) {
    return <p className="text-sm text-muted-foreground">Yükleniyor…</p>;
  }

  const compareRows: CompareRow[] = [
    ...compareExtra,
    ...variants
      .filter((v) => v.id != null && selected.has(v.id))
      .map((v) => ({
        ...v,
        urunAd: detail.ad,
        urunId: detail.id,
        ayar: detail.ayar,
      })),
  ];
  const uniqueCompare = Array.from(
    new Map(
      compareRows.filter((r) => r.id != null).map((r) => [r.id!, r]),
    ).values(),
  );

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">{detail.ad}</h1>
        <p className="text-sm text-muted-foreground">
          {detail.platform_kodu || "—"} · {detail.kategori || "—"} ·{" "}
          {detail.ayar || "—"}
        </p>
        {detail.aciklama ? (
          <p className="max-w-prose text-sm text-muted-foreground">
            {detail.aciklama}
          </p>
        ) : null}
      </header>

      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="kanal" className="text-xs text-muted-foreground">
            Satış kanalı
          </label>
          <select
            id="kanal"
            className="h-10 rounded-md border border-border bg-background px-2 text-sm"
            value={channelId ?? ""}
            onChange={(e) => setChannelId(Number(e.target.value) || null)}
          >
            {channels.length === 0 ? (
              <option value="">Kanal yok</option>
            ) : (
              channels.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.ad || c.kod}
                </option>
              ))
            )}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="gram" className="text-xs text-muted-foreground">
            Gram
          </label>
          <select
            id="gram"
            className="h-10 rounded-md border border-border bg-background px-2 text-sm"
            value={gramFilter}
            onChange={(e) => setGramFilter(e.target.value)}
          >
            <option value="">Tümü</option>
            {gramOptions.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="renk" className="text-xs text-muted-foreground">
            Renk / çeşit
          </label>
          <select
            id="renk"
            className="h-10 rounded-md border border-border bg-background px-2 text-sm"
            value={renkFilter}
            onChange={(e) => setRenkFilter(e.target.value)}
          >
            <option value="">Tümü</option>
            {renkOptions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addToCompare}
          disabled={selected.size === 0}
        >
          Karşılaştırmaya ekle
        </Button>
      </div>

      {message ? (
        <p className="text-sm text-foreground" role="status">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-2 pr-2 font-medium"> </th>
              <th className="py-2 pr-3 font-medium">SKU</th>
              <th className="py-2 pr-3 text-right font-medium tabular-nums">
                Gram
              </th>
              <th className="py-2 pr-3 font-medium">Renk</th>
              <th className="py-2 pr-3 font-medium">Beden</th>
              <th className="py-2 font-medium">İşlem</th>
            </tr>
          </thead>
          <tbody>
            {variants.map((v) => {
              const vid = v.id;
              if (vid == null) return null;
              return (
              <tr key={vid} className="border-b border-border">
                <td className="py-2 pr-2">
                  <input
                    type="checkbox"
                    checked={selected.has(vid)}
                    onChange={() => toggle(vid)}
                    aria-label={`Seç ${v.sku}`}
                  />
                </td>
                <td className="py-2 pr-3 font-mono text-xs">{v.sku}</td>
                <td className="py-2 pr-3 text-right tabular-nums">
                  {v.gram ?? "—"}
                </td>
                <td className="py-2 pr-3">{v.renk || "—"}</td>
                <td className="py-2 pr-3">{v.beden || "—"}</td>
                <td className="py-2">
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      disabled={pending || !channelId}
                      onClick={() => orderVariant(vid)}
                    >
                      Sipariş
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={pending}
                      onClick={() => rfqVariant(vid)}
                    >
                      Teklif iste
                    </Button>
                  </div>
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {uniqueCompare.length >= 2 ? (
        <section className="flex flex-col gap-3 border-t border-border pt-6">
          <h2 className="text-base font-semibold tracking-tight">
            Karşılaştırma
          </h2>
          <p className="text-xs text-muted-foreground">
            Gram/çeşit filtresi + seçim — tedarikçi bilgisi yok.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[32rem] border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="py-2 pr-3 font-medium">Ürün</th>
                  <th className="py-2 pr-3 font-medium">SKU</th>
                  <th className="py-2 pr-3 font-medium">Ayar</th>
                  <th className="py-2 pr-3 text-right font-medium tabular-nums">
                    Gram
                  </th>
                  <th className="py-2 pr-3 font-medium">Renk</th>
                  <th className="py-2 font-medium">Beden</th>
                </tr>
              </thead>
              <tbody>
                {uniqueCompare.map((r) => (
                  <tr key={r.id} className="border-b border-border">
                    <td className="py-2 pr-3">{r.urunAd}</td>
                    <td className="py-2 pr-3 font-mono text-xs">{r.sku}</td>
                    <td className="py-2 pr-3">{r.ayar || "—"}</td>
                    <td className="py-2 pr-3 text-right tabular-nums">
                      {r.gram ?? "—"}
                    </td>
                    <td className="py-2 pr-3">{r.renk || "—"}</td>
                    <td className="py-2">{r.beden || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
        <p className="text-xs text-muted-foreground">
          Karşılaştırma için en az iki varyant seçin.
        </p>
      )}
    </div>
  );
}
