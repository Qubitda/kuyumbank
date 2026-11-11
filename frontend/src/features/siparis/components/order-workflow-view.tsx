"use client";

import React, { useState, useEffect } from "react";
import { siparisService } from "../services";
import type { BuyerCart, BuyerOrder } from "../types";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  ShoppingCart,
  Package,
  AlertCircle,
  RefreshCw,
  Trash2,
  Eye,
  CheckCircle2,
} from "lucide-react";

export function OrderWorkflowView() {
  const [activeTab, setActiveTab] = useState<"cart" | "orders">("cart");

  const [cart, setCart] = useState<BuyerCart | null>(null);
  const [orders, setOrders] = useState<BuyerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedOrder, setSelectedOrder] = useState<BuyerOrder | null>(null);
  const [orderDetailOpen, setOrderDetailOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [isSubmittingCheckout, setIsSubmittingCheckout] = useState(false);

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [cartData, ordersData] = await Promise.allSettled([
        siparisService.getMyCart(),
        siparisService.getOrders(),
      ]);

      if (cartData.status === "fulfilled") {
        setCart(cartData.value);
      }
      if (ordersData.status === "fulfilled") {
        setOrders(ordersData.value || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sipariş verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleCheckout = async () => {
    setIsSubmittingCheckout(true);
    setError(null);
    try {
      const createdOrder = await siparisService.checkout();
      await refreshData();
      setActiveTab("orders");
      setSelectedOrder(createdOrder);
      setOrderDetailOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checkout işlemi başarısız.");
    } finally {
      setIsSubmittingCheckout(false);
    }
  };

  const handleRemoveLine = async (lineId: number) => {
    try {
      await siparisService.removeCartLine(lineId);
      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Satır silinemedi.");
    }
  };

  const handleOpenOrderDetail = async (orderId: number) => {
    setLoadingDetail(true);
    setOrderDetailOpen(true);
    try {
      const detail = await siparisService.getOrderDetail(orderId);
      setSelectedOrder(detail);
    } catch {
      const basic = orders.find((o) => o.id === orderId);
      if (basic) setSelectedOrder(basic);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCancelOrder = async (orderId: number) => {
    try {
      await siparisService.cancelOrder(orderId);
      await refreshData();
      if (selectedOrder && selectedOrder.id === orderId) {
        setSelectedOrder((prev) => (prev ? { ...prev, durum: "IPTAL" } : null));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sipariş iptal edilemedi.");
    }
  };

  const renderDurumBadge = (durum: string) => {
    switch (durum) {
      case "ONAYLANDI":
      case "TAMAMLANDI":
        return <Badge variant="success">{durum}</Badge>;
      case "IPTAL":
      case "REDDEDILDI":
        return <Badge variant="destructive">{durum}</Badge>;
      case "BEKLEMEDE":
      case "HAZIRLANIYOR":
      case "SEVKIYAT":
        return <Badge variant="warning">{durum}</Badge>;
      default:
        return <Badge variant="outline">{durum}</Badge>;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık ve Sekme Değiştirici */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Sipariş & Sepet Akışı
          </h1>
          <p className="text-xs text-muted-foreground">
            Quote kilitli sepet satırları, checkout snapshot'ı ve sipariş takip yüzeyi.
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-[6px] border border-border bg-muted/40 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("cart")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "cart"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <ShoppingCart className="h-3.5 w-3.5" />
            <span>Aktif Sepet ({cart?.line_count ?? 0})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("orders")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "orders"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Package className="h-3.5 w-3.5" />
            <span>Sipariş Geçmişi ({orders.length})</span>
          </button>
        </div>
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
            onClick={refreshData}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      {/* İçerik: Sepet veya Siparişler */}
      {loading ? (
        <div className="flex h-48 w-full items-center justify-center">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Veriler yükleniyor…</span>
          </div>
        </div>
      ) : activeTab === "cart" ? (
        <div className="flex flex-col gap-6">
          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            {!cart || cart.lines.length === 0 ? (
              <div className="flex h-48 flex-col items-center justify-center gap-2 text-center p-6">
                <ShoppingCart className="h-8 w-8 text-muted-foreground opacity-50" />
                <p className="text-sm font-medium text-foreground">Sepetiniz boş</p>
                <p className="text-xs text-muted-foreground max-w-sm">
                  Katalogdan seçtiğiniz ürün varyantları için oluşturulan quote tekliflerini sepete ekleyebilirsiniz.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">Satır No</TableHead>
                    <TableHead>Varyant ID</TableHead>
                    <TableHead>Quote Kilit No</TableHead>
                    <TableHead className="text-right">Miktar</TableHead>
                    <TableHead className="text-right">Birim Fiyat (Vergisiz)</TableHead>
                    <TableHead>Para Birimi</TableHead>
                    <TableHead>Kilit Son Kullanma</TableHead>
                    <TableHead className="text-right">İşlem</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cart.lines.map((line) => (
                    <TableRow key={line.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        #{line.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-medium">
                        #{line.varyant_id}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {line.quote_id ? `Q-${line.quote_id}` : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums text-foreground">
                        {line.miktar} {line.birim || "ADET"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums text-foreground font-medium">
                        {formatMoney(line.birim_fiyat_vergisiz, line.para_birimi)}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {line.para_birimi}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {line.gecerlilik_sonu ? formatDateTime(line.gecerlilik_sonu) : "Süresiz"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveLine(line.id)}
                          className="h-8 w-8 text-destructive hover:bg-destructive/10"
                          aria-label="Satırı sepetten sil"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>

          {/* Checkout Aksiyon Paneli - Tek Primary Buton Kuralı */}
          {cart && cart.lines.length > 0 && (
            <div className="flex items-center justify-between rounded-[8px] border border-border bg-card p-4">
              <div className="text-xs text-muted-foreground">
                <span>Checkout anında fiyat snapshot'ı alınarak değişmez hale getirilir.</span>
              </div>
              <Button
                type="button"
                onClick={handleCheckout}
                disabled={isSubmittingCheckout}
                className="gap-2"
              >
                <CheckCircle2 className="h-4 w-4" />
                <span>{isSubmittingCheckout ? "Oluşturuluyor…" : "Siparişi Tamamla (Checkout)"}</span>
              </Button>
            </div>
          )}
        </div>
      ) : (
        /* Sipariş Geçmişi Tablosu */
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          {orders.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center gap-2 text-center p-6">
              <Package className="h-8 w-8 text-muted-foreground opacity-50" />
              <p className="text-sm font-medium text-foreground">Kayıtlı sipariş bulunamadı</p>
              <p className="text-xs text-muted-foreground max-w-sm">
                Tamamlanan checkout işlemleri bu tabloda immutable snapshot kaydı olarak listelenir.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Sipariş No</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">Kalem Sayısı</TableHead>
                  <TableHead>Tarih</TableHead>
                  <TableHead className="text-right">İşlem</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-mono text-xs font-semibold text-foreground">
                      #{order.id}
                    </TableCell>
                    <TableCell>{renderDurumBadge(order.durum)}</TableCell>
                    <TableCell className="text-right font-mono tabular-nums">
                      {order.line_count}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDateTime(order.olusturma_tarihi)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenOrderDetail(order.id)}
                        className="h-8 text-xs gap-1.5"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>Detay</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      )}

      {/* Sipariş Detay ve İptal Dialog */}
      <Dialog open={orderDetailOpen} onOpenChange={setOrderDetailOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Sipariş #{selectedOrder?.id}</DialogTitle>
            <DialogDescription>
              Tarih: {selectedOrder?.olusturma_tarihi ? formatDateTime(selectedOrder.olusturma_tarihi) : "—"} ·{" "}
              Durum: {selectedOrder?.durum}
            </DialogDescription>
          </DialogHeader>

          {loadingDetail ? (
            <div className="flex h-32 items-center justify-center">
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          ) : selectedOrder ? (
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Fiyat Snapshot Satırları (Değişmez Snapshot)
                </span>
                {renderDurumBadge(selectedOrder.durum)}
              </div>

              {selectedOrder.lines && selectedOrder.lines.length > 0 ? (
                <div className="rounded-[6px] border border-border overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Varyant</TableHead>
                        <TableHead className="text-right">Miktar</TableHead>
                        <TableHead className="text-right">Snapshot Birim Fiyat</TableHead>
                        <TableHead className="text-right">Satır Tutarı</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedOrder.lines.map((l) => (
                        <TableRow key={l.id}>
                          <TableCell className="font-mono text-xs">
                            #{l.varyant_id}
                          </TableCell>
                          <TableCell className="text-right font-mono tabular-nums">
                            {l.miktar} {l.birim}
                          </TableCell>
                          <TableCell className="text-right font-mono tabular-nums">
                            {formatMoney(l.snapshot_birim_fiyat_vergisiz, l.para_birimi)}
                          </TableCell>
                          <TableCell className="text-right font-mono tabular-nums font-semibold">
                            {formatMoney(l.snapshot_satir_tutari_vergisiz, l.para_birimi)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground py-2">
                  Kalem bilgisi yüklenemedi.
                </p>
              )}

              {/* Sipariş İptal Aksiyonu (Yalnızca izin verilen durumlarda) */}
              {selectedOrder.allowed_actions?.includes("cancel") && (
                <div className="border-t border-border pt-4 flex justify-end">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleCancelOrder(selectedOrder.id)}
                  >
                    Siparişi İptal Et (Stok İade)
                  </Button>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
