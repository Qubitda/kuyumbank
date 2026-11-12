"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { fiyatlamaService } from "../services";
import type { SupplierRfq, SupplierOffer } from "../types";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Briefcase,
  FileCheck2,
  RefreshCw,
  AlertCircle,
  Plus,
  Send,
  EyeOff,
  CheckCircle2,
  Sparkles,
  Layers,
} from "lucide-react";

const offerSchema = z.object({
  varyant_id: z.number({ message: "Varyant ID zorunludur" }),
  birim_fiyat: z.string().trim().min(1, "Birim teklif fiyatı zorunludur"),
  para_birimi: z.string(),
  teslim_gunu: z.number().optional(),
});

type OfferFormValues = z.infer<typeof offerSchema>;

const buyerRfqSchema = z.object({
  baslik: z.string().trim().min(3, "Talep başlığı en az 3 karakter olmalıdır"),
  talep_tipi: z.enum(["STANDART", "KATALOG_DISI", "OZEL_URETIM"]),
  hedef_ayar: z.string().trim().min(1, "Ayar bilgisi zorunludur (örn: 14, 18, 22)"),
  hedef_gram: z.string().trim().min(1, "Hedef gram zorunludur"),
  miktar: z.string().trim().min(1, "Talep adedi zorunludur"),
  aciklama: z.string().trim().optional(),
});

type BuyerRfqFormValues = z.infer<typeof buyerRfqSchema>;

export function SupplierRfqOffersView() {
  const [activeTab, setActiveTab] = useState<"rfqs" | "offers" | "buyer_rfqs">("rfqs");

  const [rfqs, setRfqs] = useState<SupplierRfq[]>([]);
  const [offers, setOffers] = useState<SupplierOffer[]>([]);
  const [buyerRfqs, setBuyerRfqs] = useState<SupplierRfq[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [offerModalOpen, setOfferModalOpen] = useState(false);
  const [selectedRfq, setSelectedRfq] = useState<SupplierRfq | null>(null);

  const [buyerRfqModalOpen, setBuyerRfqModalOpen] = useState(false);

  // Tedarikçi Teklif Formu
  const {
    register: registerOffer,
    handleSubmit: handleOfferSubmit,
    reset: resetOffer,
    setValue: setOfferValue,
    formState: { errors: offerErrors, isSubmitting: isOfferSubmitting },
  } = useForm<OfferFormValues>({
    resolver: zodResolver(offerSchema),
    defaultValues: {
      varyant_id: 1,
      birim_fiyat: "",
      para_birimi: "TRY",
      teslim_gunu: 3,
    },
  });

  // Alıcı Özel RFQ Formu
  const {
    register: registerBuyerRfq,
    handleSubmit: handleBuyerRfqSubmit,
    reset: resetBuyerRfq,
    formState: { errors: buyerRfqErrors, isSubmitting: isBuyerRfqSubmitting },
  } = useForm<BuyerRfqFormValues>({
    resolver: zodResolver(buyerRfqSchema),
    defaultValues: {
      baslik: "",
      talep_tipi: "OZEL_URETIM",
      hedef_ayar: "14",
      hedef_gram: "25.00",
      miktar: "1",
      aciklama: "",
    },
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rfqRes, offerRes, buyerRfqRes] = await Promise.allSettled([
        fiyatlamaService.getSupplierRfqs(),
        fiyatlamaService.getSupplierOffers(),
        fiyatlamaService.getBuyerRfqs(),
      ]);

      if (rfqRes.status === "fulfilled") {
        setRfqs(rfqRes.value?.results || []);
      }
      if (offerRes.status === "fulfilled") {
        setOffers(offerRes.value?.results || []);
      }
      if (buyerRfqRes.status === "fulfilled") {
        setBuyerRfqs(buyerRfqRes.value?.results || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tedarikçi verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenOfferModal = (rfq: SupplierRfq) => {
    setSelectedRfq(rfq);
    const firstVariantId = rfq.lines?.[0]?.varyant_id || 1;
    setOfferValue("varyant_id", firstVariantId);
    setOfferModalOpen(true);
  };

  const onOfferSubmit = async (data: OfferFormValues) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await fiyatlamaService.createSupplierOffer({
        rfq_id: selectedRfq?.id,
        varyant_id: Number(data.varyant_id),
        birim_fiyat: data.birim_fiyat,
        para_birimi: data.para_birimi,
        teslim_gunu: data.teslim_gunu ? Number(data.teslim_gunu) : undefined,
      });
      setOfferModalOpen(false);
      resetOffer();
      setSuccessMsg("Taslak teklif başarıyla oluşturuldu.");
      await fetchData();
      setActiveTab("offers");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teklif oluşturulamadı.");
    }
  };

  const onBuyerRfqSubmit = async (data: BuyerRfqFormValues) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await fiyatlamaService.createBuyerRfq({
        baslik: data.baslik,
        talep_tipi: data.talep_tipi,
        lines: [
          {
            miktar: data.miktar,
            hedef_ayar: data.hedef_ayar,
            hedef_gram: data.hedef_gram,
            aciklama: data.aciklama,
          },
        ],
      });
      setBuyerRfqModalOpen(false);
      resetBuyerRfq();
      setSuccessMsg("Özel üretim / RFQ talebiniz taslak olarak oluşturuldu.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Özel talep oluşturulamadı.");
    }
  };

  const handleSendBuyerRfq = async (id: number) => {
    try {
      await fiyatlamaService.sendBuyerRfq(id);
      setSuccessMsg("RFQ talebiniz tedarikçi havuzuna başarıyla yayınlandı.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "RFQ yayına gönderilemedi.");
    }
  };

  const handleSubmitOffer = async (id: number) => {
    try {
      await fiyatlamaService.submitSupplierOffer(id);
      setSuccessMsg("Teklif onay için başarıyla sisteme iletildi.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teklif iletilemedi.");
    }
  };

  const handleDeactivateOffer = async (id: number) => {
    try {
      await fiyatlamaService.deactivateSupplierOffer(id);
      setSuccessMsg("Teklif pasif hale getirildi.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teklif pasifleştirilemedi.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık ve Sekmeler */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Tedarikçi Portalı & Özel Tasarım / RFQ
          </h1>
          <p className="text-xs text-muted-foreground">
            Alıcı özel üretim talepleri (RFQ) ve tedarikçi teklif havuzu (Kör Havuz: Alıcı kimliği gizlidir).
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-[6px] border border-border bg-muted/40 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("rfqs")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "rfqs"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Briefcase className="h-3.5 w-3.5" />
            <span>Açık RFQ Havuzu ({rfqs.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("offers")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "offers"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileCheck2 className="h-3.5 w-3.5" />
            <span>Verdiğim Teklifler ({offers.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("buyer_rfqs")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "buyer_rfqs"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Özel Taleplerim ({buyerRfqs.length})</span>
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 rounded-[6px] border border-border bg-muted/60 p-3 text-xs text-foreground font-medium">
          <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

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
            onClick={fetchData}
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
            <span>Tedarikçi ve RFQ verileri alınıyor…</span>
          </div>
        </div>
      ) : activeTab === "rfqs" ? (
        /* Tedarikçi Açık RFQ Havuzu */
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <EyeOff className="h-4 w-4" />
            <span>Kör Havuz: Alıcı firma kimliği ve unvanı platform tarafından gizlenmiştir.</span>
          </div>

          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            {rfqs.length === 0 ? (
              <div className="p-8 text-center text-xs text-muted-foreground">
                Şu an açık RFQ satın alma talebi bulunmamaktadır.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">RFQ ID</TableHead>
                    <TableHead>Talep Tipi</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead className="text-right">Kalem Adedi</TableHead>
                    <TableHead className="text-right">İşlem</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rfqs.map((rfq) => (
                    <TableRow key={rfq.id}>
                      <TableCell className="font-mono text-xs font-semibold">
                        RFQ-#{rfq.id}
                      </TableCell>
                      <TableCell className="text-xs font-medium">
                        {rfq.talep_tipi || "STANDART_ALIM"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {rfq.durum}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums text-xs">
                        {rfq.lines?.length || 1}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleOpenOfferModal(rfq)}
                          className="h-8 text-xs gap-1.5"
                        >
                          <Plus className="h-3.5 w-3.5" />
                          <span>Teklif Ver</span>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </div>
      ) : activeTab === "offers" ? (
        /* Tedarikçi Tekliflerim Tablosu */
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          {offers.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Henüz verilmiş bir teklif kaydınız bulunmamaktadır.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Teklif ID</TableHead>
                  <TableHead>Varyant</TableHead>
                  <TableHead className="text-right">Birim Teklif</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {offers.map((offer) => {
                  const actions = offer.allowed_actions || [];
                  return (
                    <TableRow key={offer.id}>
                      <TableCell className="font-mono text-xs font-semibold">
                        OFFER-#{offer.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        Varyant #{offer.varyant_id}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums font-semibold text-foreground">
                        {offer.birim_fiyat ? formatMoney(offer.birim_fiyat, offer.para_birimi) : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            offer.durum === "ONAYLANDI"
                              ? "success"
                              : offer.durum === "PASIF"
                              ? "destructive"
                              : offer.durum === "GONDERILDI"
                              ? "default"
                              : "outline"
                          }
                          className="font-mono text-[10px]"
                        >
                          {offer.durum}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {actions.includes("submit") && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => handleSubmitOffer(offer.id)}
                              className="h-8 text-xs gap-1"
                            >
                              <Send className="h-3.5 w-3.5" />
                              <span>Sisteme Gönder</span>
                            </Button>
                          )}
                          {actions.includes("deactivate") && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeactivateOffer(offer.id)}
                              className="h-8 text-xs text-destructive hover:bg-destructive/10"
                            >
                              Geri Çek
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </div>
      ) : (
        /* Alıcı Özel Tasarım / RFQ Taleplerim (F10-020, F10-022) */
        <div className="flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground">
              Katalogda bulunmayan özel ayar, gram veya özel tasarım mücevher taleplerinizi havuzda yayınlayın.
            </span>
            <Button
              size="sm"
              onClick={() => setBuyerRfqModalOpen(true)}
              className="gap-1.5 h-8 text-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Yeni Özel Talep / RFQ Başlat</span>
            </Button>
          </div>

          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            {buyerRfqs.length === 0 ? (
              <div className="p-8 text-center text-xs text-muted-foreground">
                Kayıtlı özel üretim veya RFQ talebiniz bulunmamaktadır.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">Talep No</TableHead>
                    <TableHead>Başlık</TableHead>
                    <TableHead>Tür</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead className="text-right">Kalem Sayısı</TableHead>
                    <TableHead className="text-right">İşlem</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {buyerRfqs.map((b) => {
                    const actions = b.allowed_actions || [];
                    return (
                      <TableRow key={b.id}>
                        <TableCell className="font-mono text-xs font-semibold">
                          #{b.id}
                        </TableCell>
                        <TableCell className="font-medium text-foreground">
                          {b.baslik || "Özel Mücevher Talebi"}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="font-mono text-[10px]">
                            {b.talep_tipi}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={b.durum === "GONDERILDI" ? "default" : "outline"}
                            className="font-mono text-[10px]"
                          >
                            {b.durum}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono tabular-nums text-xs">
                          {b.lines?.length || 1}
                        </TableCell>
                        <TableCell className="text-right">
                          {actions.includes("send") ? (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => handleSendBuyerRfq(b.id)}
                              className="h-7 text-xs gap-1"
                            >
                              <Send className="h-3 w-3" />
                              <span>Havuzda Yayınla</span>
                            </Button>
                          ) : (
                            <span className="text-[11px] text-muted-foreground font-medium">
                              {b.durum === "GONDERILDI" ? "Tedarikçilere Açık" : "İşlemde"}
                            </span>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </div>
        </div>
      )}

      {/* Tedarikçi Teklif Verme Dialog */}
      <Dialog open={offerModalOpen} onOpenChange={setOfferModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>RFQ-#{selectedRfq?.id} İçin Teklif Hazırla</DialogTitle>
            <DialogDescription>
              Birim maliyet ve teslim gün süresi belirterek teklif sunun.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleOfferSubmit(onOfferSubmit)} className="flex flex-col gap-4 pt-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="offer-var">Hedef Varyant ID</Label>
              <Input
                id="offer-var"
                type="number"
                disabled={isOfferSubmitting}
                {...registerOffer("varyant_id", { valueAsNumber: true })}
              />
              {offerErrors.varyant_id && (
                <span className="text-[11px] text-destructive">
                  {offerErrors.varyant_id.message}
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="offer-price">Birim Fiyat</Label>
                <Input
                  id="offer-price"
                  placeholder="Örn: 2450.00"
                  disabled={isOfferSubmitting}
                  {...registerOffer("birim_fiyat")}
                />
                {offerErrors.birim_fiyat && (
                  <span className="text-[11px] text-destructive">
                    {offerErrors.birim_fiyat.message}
                  </span>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="offer-curr">Para Birimi</Label>
                <select
                  id="offer-curr"
                  className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  disabled={isOfferSubmitting}
                  {...registerOffer("para_birimi")}
                >
                  <option value="TRY">TRY</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="offer-days">Teslim Süresi (İş Günü)</Label>
              <Input
                id="offer-days"
                type="number"
                placeholder="Örn: 3"
                disabled={isOfferSubmitting}
                {...registerOffer("teslim_gunu", { valueAsNumber: true })}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setOfferModalOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isOfferSubmitting}>
                {isOfferSubmitting ? "Kaydediliyor…" : "Teklifi Oluştur"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Alıcı Özel Talep / RFQ Oluşturma Dialog */}
      <Dialog open={buyerRfqModalOpen} onOpenChange={setBuyerRfqModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Yeni Özel Üretim / RFQ Talebi</DialogTitle>
            <DialogDescription>
              Katalog dışı veya özel tasarım mücevher siparişi için tedarikçi havuzuna talep açın.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleBuyerRfqSubmit(onBuyerRfqSubmit)} className="flex flex-col gap-4 pt-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rfq-title">Talep Başlığı</Label>
              <Input
                id="rfq-title"
                placeholder="Örn: 22 Ayar Özel Burma Bilezik Koleksiyonu"
                disabled={isBuyerRfqSubmitting}
                {...registerBuyerRfq("baslik")}
              />
              {buyerRfqErrors.baslik && (
                <span className="text-[11px] text-destructive">
                  {buyerRfqErrors.baslik.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rfq-type">Talep Türü</Label>
              <select
                id="rfq-type"
                className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                disabled={isBuyerRfqSubmitting}
                {...registerBuyerRfq("talep_tipi")}
              >
                <option value="OZEL_URETIM">ÖZEL ÜRETİM / TASARIM</option>
                <option value="KATALOG_DISI">KATALOG DIŞI MODEL TALEBİ</option>
                <option value="STANDART">STANDART TOPLU ALIM</option>
              </select>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-ayar">Hedef Ayar</Label>
                <Input
                  id="rfq-ayar"
                  placeholder="Örn: 14, 22"
                  disabled={isBuyerRfqSubmitting}
                  {...registerBuyerRfq("hedef_ayar")}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-gram">Hedef Gram</Label>
                <Input
                  id="rfq-gram"
                  placeholder="Örn: 35.50"
                  disabled={isBuyerRfqSubmitting}
                  {...registerBuyerRfq("hedef_gram")}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-qty">Adet</Label>
                <Input
                  id="rfq-qty"
                  placeholder="Örn: 5"
                  disabled={isBuyerRfqSubmitting}
                  {...registerBuyerRfq("miktar")}
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rfq-desc">Tasarım / İşçilik Açıklaması</Label>
              <Input
                id="rfq-desc"
                placeholder="Örn: Mat rodajlı, el işçiliği kalem işlemeli"
                disabled={isBuyerRfqSubmitting}
                {...registerBuyerRfq("aciklama")}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setBuyerRfqModalOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isBuyerRfqSubmitting}>
                {isBuyerRfqSubmitting ? "Oluşturuluyor…" : "Talebi Kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
