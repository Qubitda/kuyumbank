"use client";

import React, { useState, useEffect } from "react";
import { urunlerService } from "../services";
import { fiyatlamaService, rememberQuoteId } from "@/features/fiyatlama";
import { siparisService } from "@/features/siparis";
import { tanimlarService } from "@/features/tanimlar";
import type { BuyerCatalogItem, BuyerCatalogDetail } from "../types";
import { formatGram, formatMoney } from "@/lib/format";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Search, Eye, AlertCircle, RefreshCw, Gem, Tag, ShoppingCart, Check, Scale } from "lucide-react";
import { VariantCompareModal } from "./variant-compare-modal";

export function CatalogView() {
  const [items, setItems] = useState<BuyerCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const [selectedProduct, setSelectedProduct] = useState<BuyerCatalogDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);

  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);
  const [compareModalOpen, setCompareModalOpen] = useState(false);

  const toggleCompare = (id: number) => {
    setSelectedForCompare((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : prev.length < 4 ? [...prev, id] : prev
    );
  };
  const [quoteState, setQuoteState] = useState<
    Record<
      number,
      {
        loading: boolean;
        price?: string;
        currency?: string;
        quoteId?: number;
        added?: boolean;
        error?: string;
      }
    >
  >({});

  const handleGetQuote = async (variantId: number) => {
    setQuoteState((prev) => ({
      ...prev,
      [variantId]: { loading: true },
    }));
    try {
      const channels = await tanimlarService.getSalesChannels();
      const channelId = Array.isArray(channels) ? channels[0]?.id : undefined;
      if (!channelId) {
        throw new Error("Satış kanalı bulunamadı. Quote için satis_kanali_id zorunlu.");
      }
      const quote = await fiyatlamaService.createQuote({
        varyant_id: variantId,
        satis_kanali_id: channelId,
      });
      const price = quote.toplam_vergisiz || quote.gram_basi_vergisiz || quote.birim_fiyat;
      if (!price) {
        throw new Error("Backend fiyat alanı dönmedi.");
      }
      rememberQuoteId(quote.id);
      setQuoteState((prev) => ({
        ...prev,
        [variantId]: {
          loading: false,
          price,
          currency: quote.para_birimi,
          quoteId: quote.id,
        },
      }));
    } catch (err) {
      setQuoteState((prev) => ({
        ...prev,
        [variantId]: {
          loading: false,
          error: err instanceof Error ? err.message : "Fiyat alınamadı",
        },
      }));
    }
  };

  const handleAddToCart = async (variantId: number, quoteId: number) => {
    try {
      await siparisService.addCartLine(quoteId, "1");
      setQuoteState((prev) => ({
        ...prev,
        [variantId]: { ...prev[variantId], added: true },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sepete eklenemedi");
    }
  };

  const fetchCatalog = (q = "") => {
    setLoading(true);
    setError(null);
    const params = q ? { q } : undefined;
    urunlerService
      .getCatalog(params)
      .then((data) => {
        setItems(data?.results || []);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Katalog verisi alınamadı.");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCatalog(searchQuery);
  };

  const handleOpenDetail = async (id: number) => {
    setLoadingDetail(true);
    setDetailOpen(true);
    try {
      const detail = await urunlerService.getProductDetail(id);
      setSelectedProduct(detail);
    } catch {
      // Backend bağlantısı yoksa listedeki temel veriyle göster
      const basic = items.find((i) => i.id === id);
      if (basic) {
        setSelectedProduct({
          id: basic.id,
          ad: basic.ad,
          platform_kodu: basic.platform_kodu,
          kategori: basic.kategori,
          ayar: basic.ayar,
          fiyat_tipi: basic.fiyat_tipi,
          allowed_actions: basic.allowed_actions,
          varyantlar: [],
        });
      }
    } finally {
      setLoadingDetail(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Üst Başlık ve Arama */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Ürün Kataloğu
          </h1>
          <p className="text-xs text-muted-foreground">
            Platform onaylı mücevher ve altın ürün varyantları. Kör havuz: Tedarikçi ve maliyet gizlidir.
          </p>
        </div>

        {/* Arama Formu */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-sm w-full">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Kod veya ürün adı ara…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
          <Button type="submit" variant="secondary" size="sm" className="h-9">
            Filtrele
          </Button>
        </form>
      </div>

      {/* Hata Durumu */}
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
            onClick={() => fetchCatalog(searchQuery)}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      {/* Katalog Tablosu */}
      <div className="rounded-[8px] border border-border bg-card overflow-hidden">
        {loading ? (
          <div className="flex h-48 w-full items-center justify-center">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Katalog verileri yükleniyor…</span>
            </div>
          </div>
        ) : items.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center gap-2 text-center p-6">
            <Gem className="h-8 w-8 text-muted-foreground opacity-50" />
            <p className="text-sm font-medium text-foreground">Katalogda ürün bulunamadı</p>
            <p className="text-xs text-muted-foreground max-w-md">
              Kriterlere uygun yayınlı ve onaylı ürün kaydı bulunmuyor veya backend bağlantısı bekleniyor.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[40px]"></TableHead>
                <TableHead className="w-[120px]">Platform Kodu</TableHead>
                <TableHead>Ürün Adı</TableHead>
                <TableHead>Kategori</TableHead>
                <TableHead>Ayar / Milyem</TableHead>
                <TableHead className="text-right">Varyant Sayısı</TableHead>
                <TableHead>Fiyat Modeli</TableHead>
                <TableHead className="text-right">İşlem</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="w-[40px] pr-0">
                    <input
                      type="checkbox"
                      checked={selectedForCompare.includes(item.id)}
                      onChange={() => toggleCompare(item.id)}
                      className="h-4 w-4 rounded-[4px] border-border text-primary focus:ring-ring cursor-pointer"
                      aria-label={`${item.ad} karşılaştırma seçimi`}
                    />
                  </TableCell>
                  <TableCell className="font-mono text-xs text-foreground font-medium">
                    {item.platform_kodu}
                  </TableCell>
                  <TableCell className="font-medium text-foreground">
                    {item.ad}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {item.kategori || "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-foreground">
                    {item.ayar ? `${item.ayar} Ayar` : "—"}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums text-foreground">
                    {item.varyant_count}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono text-[11px]">
                      {item.fiyat_tipi || "ONS_BAZLI"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenDetail(item.id)}
                      className="h-8 text-xs gap-1.5"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      <span>İncele</span>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Ürün ve Varyant Detay Dialog */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedProduct?.ad || "Ürün Detayı"}</DialogTitle>
            <DialogDescription>
              Platform Kodu:{" "}
              <span className="font-mono text-foreground font-medium">
                {selectedProduct?.platform_kodu}
              </span>{" "}
              · Ayar: {selectedProduct?.ayar || "—"}
            </DialogDescription>
          </DialogHeader>

          {loadingDetail ? (
            <div className="flex h-36 items-center justify-center">
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          ) : selectedProduct ? (
            <div className="flex flex-col gap-4">
              {selectedProduct.aciklama && (
                <p className="text-xs text-muted-foreground">
                  {selectedProduct.aciklama}
                </p>
              )}

              <div className="flex flex-col gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Tanımlı Varyantlar (Kör Havuz)
                </span>

                {selectedProduct.varyantlar?.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-2">
                    Bu ürüne ait aktif varyant kaydı bulunamadı.
                  </p>
                ) : (
                  <div className="rounded-[6px] border border-border overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>SKU</TableHead>
                          <TableHead>Beden / Ölçü</TableHead>
                          <TableHead>Renk</TableHead>
                          <TableHead className="text-right">Gram</TableHead>
                          <TableHead className="text-right">Canlı Fiyat / Sepet</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedProduct.varyantlar?.map((v) => {
                          const state = quoteState[v.id];
                          return (
                            <TableRow key={v.id}>
                              <TableCell className="font-mono text-xs font-medium">
                                {v.sku}
                              </TableCell>
                              <TableCell>{v.beden || "Standart"}</TableCell>
                              <TableCell>{v.renk || "Sarı"}</TableCell>
                              <TableCell className="text-right font-mono tabular-nums">
                                {formatGram(v.gram)}
                              </TableCell>
                              <TableCell className="text-right">
                                {!state?.price ? (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleGetQuote(v.id)}
                                    disabled={state?.loading}
                                    className="h-7 text-xs gap-1"
                                  >
                                    <Tag className="h-3 w-3" />
                                    <span>{state?.loading ? "Hesaplanıyor…" : "Quote İste"}</span>
                                  </Button>
                                ) : state.added ? (
                                  <Badge variant="success" className="gap-1 font-mono text-[11px]">
                                    <Check className="h-3 w-3" />
                                    <span>Sepete Eklendi</span>
                                  </Badge>
                                ) : (
                                  <div className="flex items-center justify-end gap-2">
                                    <span className="font-mono text-xs font-semibold tabular-nums text-foreground">
                                      {formatMoney(state.price, state.currency || "TRY")}
                                    </span>
                                    <Button
                                      variant="default"
                                      size="sm"
                                      onClick={() => handleAddToCart(v.id, state.quoteId!)}
                                      className="h-7 text-xs gap-1"
                                    >
                                      <ShoppingCart className="h-3 w-3" />
                                      <span>Sepete Ekle</span>
                                    </Button>
                                  </div>
                                )}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Karşılaştırma Çubuğu (CAP-COMPARE) */}
      {selectedForCompare.length > 0 && (
        <div className="sticky bottom-4 z-20 flex items-center justify-between rounded-[8px] border border-border bg-card/95 backdrop-blur-sm p-4 shadow-lg animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="flex items-center gap-2">
            <Scale className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold text-foreground">
              {selectedForCompare.length} ürün seçildi
            </span>
            <span className="text-xs text-muted-foreground hidden sm:inline">
              (Maksimum 4 ürün karşılaştırılabilir)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedForCompare([])}
              className="h-8 text-xs"
            >
              Temizle
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => setCompareModalOpen(true)}
              className="h-8 text-xs gap-1.5"
            >
              <Scale className="h-3.5 w-3.5" />
              <span>Karşılaştır ({selectedForCompare.length})</span>
            </Button>
          </div>
        </div>
      )}

      {/* Karşılaştırma Modalı */}
      <VariantCompareModal
        open={compareModalOpen}
        onOpenChange={setCompareModalOpen}
        selectedItems={items.filter((i) => selectedForCompare.includes(i.id))}
        onRemoveItem={(id) => setSelectedForCompare((prev) => prev.filter((i) => i !== id))}
        onInspectItem={(id) => handleOpenDetail(id)}
      />
    </div>
  );
}
