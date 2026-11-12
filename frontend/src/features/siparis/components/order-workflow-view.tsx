"use client";

import React, { useState, useEffect } from "react";
import { siparisService } from "../services";
import type { BuyerCart, BuyerOrder } from "../types";
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
  MapPin,
  Building,
  CreditCard,
  FileSpreadsheet,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { firmalarService, type FirmaAdresi } from "@/features/firmalar";
import { finansService } from "@/features/finans";
import type { BulkOrderResult } from "../types";

export function OrderWorkflowView() {
  const [activeTab, setActiveTab] = useState<"cart" | "orders" | "bulk">("cart");

  const [cart, setCart] = useState<BuyerCart | null>(null);
  const [orders, setOrders] = useState<BuyerOrder[]>([]);
  const [addresses, setAddresses] = useState<FirmaAdresi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [checkoutModalOpen, setCheckoutModalOpen] = useState(false);
  const [selectedDeliveryAddr, setSelectedDeliveryAddr] = useState<number | undefined>(undefined);
  const [selectedInvoiceAddr, setSelectedInvoiceAddr] = useState<number | undefined>(undefined);
  const [orderNotes, setOrderNotes] = useState("");

  const [selectedOrder, setSelectedOrder] = useState<BuyerOrder | null>(null);
  const [orderDetailOpen, setOrderDetailOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [isSubmittingCheckout, setIsSubmittingCheckout] = useState(false);
  const [paymentMsg, setPaymentMsg] = useState<string | null>(null);

  // Toplu Sipariş State'leri
  const [bulkText, setBulkText] = useState("");
  const [bulkResult, setBulkResult] = useState<BulkOrderResult | null>(null);
  const [isSubmittingBulk, setIsSubmittingBulk] = useState(false);

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bulkText.trim()) return;
    setIsSubmittingBulk(true);
    setError(null);
    setBulkResult(null);

    // Format parse: SKU, Miktar, Birim
    const lines = bulkText.split("\n").map((l) => l.trim()).filter(Boolean);
    const rows = lines.map((line) => {
      const parts = line.split(/[,;\t]/).map((p) => p.trim());
      return {
        sku: parts[0] || "",
        miktar: parts[1] || "1",
        birim: parts[2] || "ADET",
      };
    });

    try {
      const result = await siparisService.createBulkOrder({
        satis_kanali_id: 1,
        rows,
      });
      setBulkResult(result);
      if (result.order_id) {
        await refreshData();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Toplu sipariş işlenemedi.");
    } finally {
      setIsSubmittingBulk(false);
    }
  };

  const handlePayOrder = async (orderId: number) => {
    try {
      await finansService.createPaymentIntent(orderId);
      setPaymentMsg("Ödeme niyeti başarıyla oluşturuldu. Havale / Cari Mahsup kaydı bekleniyor.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ödeme işlemi başlatılamadı.");
    }
  };

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [cartData, ordersData, addressData] = await Promise.allSettled([
        siparisService.getMyCart(),
        siparisService.getOrders(),
        firmalarService.getAddresses(),
      ]);

      if (cartData.status === "fulfilled") {
        setCart(cartData.value);
      }
      if (ordersData.status === "fulfilled") {
        setOrders(unwrapResults(ordersData.value));
      }
      if (addressData.status === "fulfilled") {
        const addrList = addressData.value?.results || [];
        setAddresses(addrList);
        const defDelivery = addrList.find((a) => a.tip === "TESLIMAT" && a.varsayilan) || addrList.find((a) => a.tip === "TESLIMAT");
        const defInvoice = addrList.find((a) => a.tip === "FATURA" && a.varsayilan) || addrList.find((a) => a.tip === "FATURA");
        if (defDelivery) setSelectedDeliveryAddr(defDelivery.id);
        if (defInvoice) setSelectedInvoiceAddr(defInvoice.id);
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

  const handleConfirmCheckout = async () => {
    setIsSubmittingCheckout(true);
    setError(null);
    try {
      // OpenAPI: POST /checkouts/ (EmptyRequest) → POST /orders/from-checkout/
      const createdOrder = await siparisService.checkout();
      setCheckoutModalOpen(false);
      setOrderNotes("");
      void selectedDeliveryAddr;
      void selectedInvoiceAddr;
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
          <button
            type="button"
            onClick={() => setActiveTab("bulk")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "bulk"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileSpreadsheet className="h-3.5 w-3.5" />
            <span>Toplu Sipariş / CSV</span>
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
                onClick={() => setCheckoutModalOpen(true)}
                disabled={isSubmittingCheckout}
                className="gap-2"
              >
                <CheckCircle2 className="h-4 w-4" />
                <span>Siparişi Tamamla (Checkout)</span>
              </Button>
            </div>
          )}
        </div>
      ) : activeTab === "orders" ? (
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
      ) : (
        /* Toplu Sipariş / Hızlı SKU Girişi (F4-081) */
        <div className="flex flex-col gap-6">
          <form
            onSubmit={handleBulkSubmit}
            className="flex flex-col gap-4 rounded-[8px] border border-border bg-card p-6"
          >
            <div className="flex flex-col gap-1 border-b border-border pb-3">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-primary" />
                <span>Hızlı Toplu Sipariş & SKU Listesi Girişi</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Toptan alımlarda her satıra bir kalem gelecek şekilde SKU, Miktar ve Birim girin (Virgül, noktalı virgül veya sekme ile ayırabilirsiniz).
              </p>
            </div>

            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-medium text-foreground">
                Kalem Listesi (Format: SKU, MIKTAR, BIRIM)
              </span>
              <textarea
                value={bulkText}
                onChange={(e) => setBulkText(e.target.value)}
                placeholder={"BLZ-22K-BURMA, 10, ADET\nYUZ-18K-TEKTAS, 5, ADET\nKLY-14K-BAGET, 20, ADET"}
                rows={6}
                className="w-full rounded-[6px] border border-input bg-background p-3 text-xs font-mono shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                disabled={isSubmittingBulk}
              />
              <span className="text-[11px] text-muted-foreground">
                Örnek: Her satıra "SKU_KODU, ADET, BIRIM" şeklinde yazın.
              </span>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="submit"
                disabled={isSubmittingBulk || !bulkText.trim()}
                className="gap-2"
              >
                <Upload className="h-4 w-4" />
                <span>{isSubmittingBulk ? "İşleniyor…" : "Toplu Siparişi Oluştur"}</span>
              </Button>
            </div>
          </form>

          {/* Toplu Sipariş Sonuç Raporu */}
          {bulkResult && (
            <div className="rounded-[8px] border border-border bg-card p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                  <span className="text-sm font-semibold text-foreground">
                    Toplu Sipariş Tamamlandı {bulkResult.order_id && `(Sipariş #${bulkResult.order_id})`}
                  </span>
                </div>
                {bulkResult.order_id && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      handleOpenOrderDetail(bulkResult.order_id!);
                    }}
                    className="text-xs gap-1.5"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    <span>Siparişi İncele</span>
                  </Button>
                )}
              </div>

              {/* Kabul Edilen Kalemler */}
              {bulkResult.accepted?.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-foreground">
                    Kabul Edilen Kalemler ({bulkResult.accepted.length})
                  </span>
                  <div className="rounded-[6px] border border-border overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[60px]">Satır</TableHead>
                          <TableHead>SKU</TableHead>
                          <TableHead className="text-right">Miktar</TableHead>
                          <TableHead>Birim</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {bulkResult.accepted.map((a, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-mono text-xs">{a.satir_no}</TableCell>
                            <TableCell className="font-mono text-xs font-medium">{a.sku}</TableCell>
                            <TableCell className="text-right font-mono tabular-nums">{a.miktar}</TableCell>
                            <TableCell className="text-xs text-muted-foreground">{a.birim || "ADET"}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}

              {/* Hatalı Kalemler */}
              {bulkResult.errors?.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-destructive">
                    Hatalı / Bulunamayan Kalemler ({bulkResult.errors.length})
                  </span>
                  <div className="rounded-[6px] border border-destructive/30 overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[60px]">Satır</TableHead>
                          <TableHead>SKU</TableHead>
                          <TableHead>Hata Açıklaması</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {bulkResult.errors.map((e, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-mono text-xs text-destructive">{e.satir_no}</TableCell>
                            <TableCell className="font-mono text-xs font-medium">{e.sku}</TableCell>
                            <TableCell className="text-xs text-destructive">{e.hata}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </div>
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

              <div className="border-t border-border pt-4 flex flex-wrap items-center justify-between gap-2">
                <div>
                  {paymentMsg ? (
                    <span className="text-xs text-primary font-medium">{paymentMsg}</span>
                  ) : (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => handlePayOrder(selectedOrder.id)}
                      className="gap-1.5 text-xs"
                    >
                      <CreditCard className="h-3.5 w-3.5" />
                      <span>Ödeme İşlemi Başlat (PaymentIntent)</span>
                    </Button>
                  )}
                </div>

                {selectedOrder.allowed_actions?.includes("cancel") && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleCancelOrder(selectedOrder.id)}
                  >
                    Siparişi İptal Et (Stok İade)
                  </Button>
                )}
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Checkout Adres ve Onay Modalı */}
      <Dialog open={checkoutModalOpen} onOpenChange={setCheckoutModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Sipariş Onayı & Teslimat Bilgisi</DialogTitle>
            <DialogDescription>
              Zırhlı kargo teslimat ve e-fatura adresinizi seçerek siparişi kesinleştirin.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 pt-2">
            {/* Teslimat Adresi Seçimi */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>Teslimat Adresi (Zırhlı Kargo)</span>
                </span>
                <Link
                  href="/profil"
                  className="text-[11px] text-primary hover:underline underline-offset-2"
                >
                  Yeni Adres Ekle
                </Link>
              </div>

              {addresses.filter((a) => a.tip === "TESLIMAT").length === 0 ? (
                <div className="rounded-[6px] border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
                  Kayıtlı teslimat adresi bulunamadı. Lütfen{" "}
                  <Link href="/profil" className="text-foreground underline">
                    Profil & Adresler
                  </Link>{" "}
                  sayfasından adres ekleyin.
                </div>
              ) : (
                <select
                  value={selectedDeliveryAddr}
                  onChange={(e) => setSelectedDeliveryAddr(Number(e.target.value))}
                  className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-xs shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  {addresses
                    .filter((a) => a.tip === "TESLIMAT")
                    .map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.il} {a.ilce ? `/ ${a.ilce}` : ""} — {a.adres}
                      </option>
                    ))}
                </select>
              )}
            </div>

            {/* Fatura Adresi Seçimi */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Building className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>Fatura Adresi</span>
                </span>
              </div>

              {addresses.filter((a) => a.tip === "FATURA").length === 0 ? (
                <div className="rounded-[6px] border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
                  Kayıtlı fatura adresi bulunamadı (Teslimat adresi kullanılacak).
                </div>
              ) : (
                <select
                  value={selectedInvoiceAddr}
                  onChange={(e) => setSelectedInvoiceAddr(Number(e.target.value))}
                  className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-xs shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  {addresses
                    .filter((a) => a.tip === "FATURA")
                    .map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.il} {a.ilce ? `/ ${a.ilce}` : ""} — {a.adres}
                      </option>
                    ))}
                </select>
              )}
            </div>

            {/* Sipariş Notu */}
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-foreground">Sipariş Notu (Opsiyonel)</span>
              <input
                type="text"
                value={orderNotes}
                onChange={(e) => setOrderNotes(e.target.value)}
                placeholder="Örn: Saat 14:00 öncesi teslimat ricası"
                className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-xs shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>

            <div className="rounded-[6px] border border-border/80 bg-muted/40 p-3 text-xs space-y-1">
              <div className="flex justify-between text-muted-foreground">
                <span>Sepetteki Kalem Adedi:</span>
                <span className="font-mono font-medium text-foreground">{cart?.line_count}</span>
              </div>
              <div className="text-[11px] text-muted-foreground">
                Onayladığınızda quote birim fiyatları dondurulur ve sipariş oluşturulur.
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCheckoutModalOpen(false)}
              >
                İptal
              </Button>
              <Button
                type="button"
                size="sm"
                disabled={isSubmittingCheckout}
                onClick={handleConfirmCheckout}
                className="gap-1.5"
              >
                <CheckCircle2 className="h-4 w-4" />
                <span>{isSubmittingCheckout ? "Oluşturuluyor…" : "Siparişi Kesinleştir"}</span>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
