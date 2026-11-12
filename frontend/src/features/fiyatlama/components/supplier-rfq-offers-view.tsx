"use client";

import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { fiyatlamaService } from "../services";
import type { SupplierOfferImportSatir, SupplierRfq } from "../types";
import { formatMoney } from "@/lib/format";
import {
  useSupplierRfqsQuery,
  useSupplierOffersQuery,
  useBuyerRfqsQuery,
  useSupplierRfqQuery,
  useFiyatlamaInvalidate,
} from "../hooks";
import { ApiError } from "@/lib/api/client";
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
  Upload,
} from "lucide-react";
import { useActionToast } from "@/hooks/use-action-toast";
import { BlindPoolCallout } from "./blind-pool-callout";
import { RfqStatusTracker } from "./rfq-status-tracker";
import { buildOzelUretimAciklama } from "../lib/ozel-uretim-aciklama";

const offerSchema = z.object({
  varyant_id: z.number({ message: "Varyant ID zorunludur" }),
  fiyat_modeli: z.enum(["ADET", "GRAM", "METAL_BAZLI"]),
  birim_fiyat: z.string().trim().min(1, "Birim teklif fiyatı zorunludur"),
  gram: z.string().trim().optional(),
  iscilik_override: z.string().trim().optional(),
  para_birimi: z.string(),
  uretim_suresi_gun: z.number().optional(),
});

type OfferFormValues = z.infer<typeof offerSchema>;

const buyerRfqSchema = z.object({
  baslik: z.string().trim().min(3, "Talep başlığı en az 3 karakter olmalıdır"),
  talep_tipi: z.enum(["STANDART", "KATALOG_DISI", "OZEL_URETIM"]),
  montur_ad: z.string().trim().optional(),
  montur_varyant_id: z.string().trim().optional(),
  tas_ozeti: z.string().trim().optional(),
  hedef_ayar: z.string().trim().min(1, "Ayar bilgisi zorunludur (örn: 14, 18, 22)"),
  hedef_gram: z.string().trim().min(1, "Hedef gram zorunludur"),
  miktar: z.string().trim().min(1, "Talep adedi zorunludur"),
  aciklama: z.string().trim().optional(),
});

type BuyerRfqFormValues = z.infer<typeof buyerRfqSchema>;

export function SupplierRfqOffersView({
  focusRfqId,
}: {
  focusRfqId?: string;
}) {
  const actionToast = useActionToast();
  const invalidateFiyatlama = useFiyatlamaInvalidate();
  const [activeTab, setActiveTab] = useState<"rfqs" | "offers" | "buyer_rfqs">("rfqs");

  const rfqsQuery = useSupplierRfqsQuery();
  const offersQuery = useSupplierOffersQuery();
  const buyerRfqsQuery = useBuyerRfqsQuery();
  const focusIdNum =
    focusRfqId && Number.isFinite(Number(focusRfqId))
      ? Number(focusRfqId)
      : undefined;
  const focusRfqQuery = useSupplierRfqQuery(focusIdNum, Boolean(focusIdNum));

  const rfqs = rfqsQuery.data?.results || [];
  const offers = offersQuery.data?.results || [];
  const buyerRfqs = buyerRfqsQuery.data?.results || [];
  const loading =
    rfqsQuery.isLoading || offersQuery.isLoading || buyerRfqsQuery.isLoading;
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [offerModalOpen, setOfferModalOpen] = useState(false);
  const [selectedRfq, setSelectedRfq] = useState<SupplierRfq | null>(null);

  const [buyerRfqModalOpen, setBuyerRfqModalOpen] = useState(false);

  const [importBusy, setImportBusy] = useState(false);
  const [importPreviewRows, setImportPreviewRows] = useState<
    SupplierOfferImportSatir[]
  >([]);
  const [importErrors, setImportErrors] = useState<
    Array<{ satir_no: number; hata: string }>
  >([]);

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
      fiyat_modeli: "GRAM",
      birim_fiyat: "",
      gram: "",
      iscilik_override: "",
      para_birimi: "TRY",
      uretim_suresi_gun: 3,
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
      montur_ad: "",
      montur_varyant_id: "",
      tas_ozeti: "",
      hedef_ayar: "14",
      hedef_gram: "25.00",
      miktar: "1",
      aciklama: "",
    },
  });

  const fetchData = async () => {
    setError(null);
    await invalidateFiyatlama();
  };

  useEffect(() => {
    const err =
      rfqsQuery.error || offersQuery.error || buyerRfqsQuery.error;
    if (err) {
      setError(
        err instanceof Error ? err.message : "Tedarikçi verileri alınamadı."
      );
    }
  }, [rfqsQuery.error, offersQuery.error, buyerRfqsQuery.error]);

  useEffect(() => {
    if (focusRfqQuery.data) {
      setSelectedRfq(focusRfqQuery.data);
      setActiveTab("rfqs");
    }
  }, [focusRfqQuery.data]);

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
      // OpenAPI: rfq_id yok (GAP-F3-06). Teklif varyant + fiyat alanları.
      await fiyatlamaService.createSupplierOffer({
        varyant_id: Number(data.varyant_id),
        fiyat_modeli: data.fiyat_modeli,
        birim_fiyat: data.birim_fiyat,
        gram: data.gram || undefined,
        iscilik_override: data.iscilik_override || undefined,
        para_birimi: data.para_birimi,
        uretim_suresi_gun: data.uretim_suresi_gun
          ? Number(data.uretim_suresi_gun)
          : undefined,
      });
      setOfferModalOpen(false);
      resetOffer();
      setSuccessMsg("Taslak teklif başarıyla oluşturuldu.");
      actionToast.success("Taslak teklif oluşturuldu");
      await fetchData();
      setActiveTab("offers");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teklif oluşturulamadı.");
      actionToast.error("Teklif oluşturulamadı", err);
    }
  };

  const onBuyerRfqSubmit = async (data: BuyerRfqFormValues) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const monturId = data.montur_varyant_id
        ? Number(data.montur_varyant_id)
        : undefined;
      const aciklama = buildOzelUretimAciklama({
        monturAd: data.montur_ad,
        monturVaryantId:
          monturId && Number.isFinite(monturId) ? monturId : undefined,
        tasOzeti: data.tas_ozeti,
        hedefAyar: data.hedef_ayar,
        hedefGram: data.hedef_gram,
        not: data.aciklama,
      });
      await fiyatlamaService.createBuyerRfq({
        baslik: data.baslik,
        talep_tipi: data.talep_tipi,
        lines: [
          {
            miktar: data.miktar,
            birim: "ADET",
            varyant_id:
              monturId && Number.isFinite(monturId) ? monturId : undefined,
            aciklama,
          },
        ],
      });
      setBuyerRfqModalOpen(false);
      resetBuyerRfq();
      setSuccessMsg("Özel üretim / RFQ talebiniz taslak olarak oluşturuldu.");
      actionToast.success("RFQ taslağı oluşturuldu");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Özel talep oluşturulamadı.");
      actionToast.error("RFQ oluşturulamadı", err);
    }
  };

  const handleSendBuyerRfq = async (id: number) => {
    try {
      await fiyatlamaService.sendBuyerRfq(id);
      setSuccessMsg("RFQ talebiniz tedarikçi havuzuna başarıyla yayınlandı.");
      actionToast.success("RFQ yayınlandı");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "RFQ yayına gönderilemedi.");
      actionToast.error("RFQ yayınlanamadı", err);
    }
  };

  const handleSubmitOffer = async (id: number) => {
    try {
      await fiyatlamaService.submitSupplierOffer(id);
      setSuccessMsg("Teklif onay için başarıyla sisteme iletildi.");
      actionToast.success("Teklif iletildi");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teklif iletilemedi.");
      actionToast.error("Teklif iletilemedi", err);
    }
  };

  const handleDeactivateOffer = async (id: number) => {
    try {
      await fiyatlamaService.deactivateSupplierOffer(id);
      setSuccessMsg("Teklif pasif hale getirildi.");
      actionToast.success("Teklif pasifleştirildi");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teklif pasifleştirilemedi.");
      actionToast.error("Teklif pasifleştirilemedi", err);
    }
  };

  const handleImportFile = async (file: File | null) => {
    if (!file) return;
    if (file.name.toLowerCase().endsWith(".pdf")) {
      setError("PDF föy henüz desteklenmiyor; CSV yükleyin.");
      actionToast.error("PDF desteklenmiyor", null);
      return;
    }
    setImportBusy(true);
    setError(null);
    try {
      const text = await file.text();
      const preview = await fiyatlamaService.previewOfferImport(text);
      setImportPreviewRows(preview.satirlar || []);
      setImportErrors(preview.hatalar || []);
      if ((preview.satirlar || []).length === 0) {
        actionToast.error("Önizlemede geçerli satır yok", null);
      } else {
        actionToast.success(
          `${preview.satirlar.length} satır hazır` +
            (preview.hatalar?.length ? `, ${preview.hatalar.length} hata` : "")
        );
      }
    } catch (err) {
      setImportPreviewRows([]);
      setImportErrors([]);
      setError(err instanceof Error ? err.message : "Föy önizleme başarısız.");
      actionToast.error("Föy önizleme başarısız", err);
    } finally {
      setImportBusy(false);
    }
  };

  const handleImportCommit = async () => {
    if (importPreviewRows.length === 0) return;
    setImportBusy(true);
    setError(null);
    try {
      const result = await fiyatlamaService.commitOfferImport(importPreviewRows);
      setSuccessMsg(`${result.created.length} taslak teklif oluşturuldu.`);
      actionToast.success("Föy commit tamam");
      setImportPreviewRows([]);
      setImportErrors([]);
      await fetchData();
    } catch (err) {
      if (err instanceof ApiError) {
        const hatalar = (err.problem as { hatalar?: typeof importErrors }).hatalar;
        if (Array.isArray(hatalar)) setImportErrors(hatalar);
      }
      setError(err instanceof Error ? err.message : "Föy commit başarısız.");
      actionToast.error("Föy commit başarısız", err);
    } finally {
      setImportBusy(false);
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
            Alıcı özel üretim talepleri (RFQ) ve tedarikçi teklif havuzu.
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

      <BlindPoolCallout role="both" />

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
        <div className="flex flex-col gap-4">
          <div className="rounded-[8px] border border-border bg-card p-4 space-y-3">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">Föy CSV içe aktarma</p>
                <p className="text-[11px] text-muted-foreground font-mono">
                  sütunlar: fiyat_modeli + (varyant_id|sku), gram, birim_fiyat — PDF yok
                </p>
              </div>
              <label className="inline-flex items-center gap-2 text-xs">
                <input
                  type="file"
                  accept=".csv,text/csv"
                  className="text-xs file:mr-2 file:rounded-[4px] file:border file:border-border file:bg-muted file:px-2 file:py-1"
                  disabled={importBusy}
                  onChange={(e) => {
                    const f = e.target.files?.[0] ?? null;
                    void handleImportFile(f);
                    e.target.value = "";
                  }}
                />
                <Upload className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
              </label>
            </div>
            {importErrors.length > 0 ? (
              <ul className="text-[11px] text-destructive space-y-0.5 font-mono">
                {importErrors.slice(0, 8).map((h) => (
                  <li key={`${h.satir_no}-${h.hata}`}>
                    satır {h.satir_no}: {h.hata}
                  </li>
                ))}
              </ul>
            ) : null}
            {importPreviewRows.length > 0 ? (
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-muted-foreground">
                  Önizleme: {importPreviewRows.length} geçerli satır → taslak teklif
                </p>
                <Button
                  type="button"
                  size="sm"
                  className="h-8 text-xs"
                  disabled={importBusy}
                  onClick={() => void handleImportCommit()}
                >
                  Commit ({importPreviewRows.length})
                </Button>
              </div>
            ) : null}
          </div>

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
                          <div className="flex flex-col gap-1.5">
                            <Badge
                              variant={b.durum === "GONDERILDI" ? "default" : "outline"}
                              className="font-mono text-[10px] w-fit"
                            >
                              {b.durum}
                            </Badge>
                            <RfqStatusTracker durum={b.durum} />
                          </div>
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
            <DialogTitle>RFQ-#{selectedRfq?.id} için teklif taslağı</DialogTitle>
            <DialogDescription>
              OpenAPI alanları: fiyat modeli, gram, birim fiyat, işçilik override.
              RFQ bağlama API&apos;de yok (GAP-F3-06) — teklif varyanta yazılır.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleOfferSubmit(onOfferSubmit)} className="flex flex-col gap-4 pt-2">
            <BlindPoolCallout role="supplier" />
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
                <Label htmlFor="offer-model">Fiyat modeli</Label>
                <select
                  id="offer-model"
                  className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-sm"
                  disabled={isOfferSubmitting}
                  {...registerOffer("fiyat_modeli")}
                >
                  <option value="GRAM">GRAM</option>
                  <option value="ADET">ADET</option>
                  <option value="METAL_BAZLI">METAL_BAZLI</option>
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="offer-gram">Gram</Label>
                <Input
                  id="offer-gram"
                  className="font-mono tabular-nums text-right"
                  placeholder="Örn: 12.500"
                  disabled={isOfferSubmitting}
                  {...registerOffer("gram")}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="offer-price">Birim fiyat</Label>
                <Input
                  id="offer-price"
                  className="font-mono tabular-nums text-right"
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
                <Label htmlFor="offer-isci">İşçilik override (gr)</Label>
                <Input
                  id="offer-isci"
                  className="font-mono tabular-nums text-right"
                  placeholder="Opsiyonel"
                  disabled={isOfferSubmitting}
                  {...registerOffer("iscilik_override")}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="offer-curr">Para birimi</Label>
                <select
                  id="offer-curr"
                  className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-sm"
                  disabled={isOfferSubmitting}
                  {...registerOffer("para_birimi")}
                >
                  <option value="TRY">TRY</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="offer-days">Üretim süresi (gün)</Label>
                <Input
                  id="offer-days"
                  type="number"
                  placeholder="Örn: 3"
                  disabled={isOfferSubmitting}
                  {...registerOffer("uretim_suresi_gun", { valueAsNumber: true })}
                />
              </div>
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
            <DialogTitle>Özel üretim akışı</DialogTitle>
            <DialogDescription>
              Montür → taş → talep. Ayar/gram first-class API alanı yok;{" "}
              <code className="font-mono text-[10px]">aciklama</code> içine
              kodlanır (GAP-F3-05).
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleBuyerRfqSubmit(onBuyerRfqSubmit)} className="flex flex-col gap-4 pt-2">
            <BlindPoolCallout role="buyer" />
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rfq-title">Talep başlığı</Label>
              <Input
                id="rfq-title"
                placeholder="Örn: 22 Ayar Özel Burma Bilezik"
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
              <Label htmlFor="rfq-type">Talep türü</Label>
              <select
                id="rfq-type"
                className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-sm"
                disabled={isBuyerRfqSubmitting}
                {...registerBuyerRfq("talep_tipi")}
              >
                <option value="OZEL_URETIM">Özel üretim / tasarım</option>
                <option value="KATALOG_DISI">Katalog dışı model</option>
                <option value="STANDART">Standart toplu alım</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-montur">1. Montür (ad)</Label>
                <Input
                  id="rfq-montur"
                  placeholder="Burma bilezik montürü"
                  disabled={isBuyerRfqSubmitting}
                  {...registerBuyerRfq("montur_ad")}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-montur-id">Montür varyant id</Label>
                <Input
                  id="rfq-montur-id"
                  inputMode="numeric"
                  placeholder="Opsiyonel katalog id"
                  className="font-mono"
                  disabled={isBuyerRfqSubmitting}
                  {...registerBuyerRfq("montur_varyant_id")}
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rfq-tas">2. Taş seçimi</Label>
              <Input
                id="rfq-tas"
                placeholder="Örn: 0.30ct baget, G-VS"
                disabled={isBuyerRfqSubmitting}
                {...registerBuyerRfq("tas_ozeti")}
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-ayar">Hedef ayar</Label>
                <Input
                  id="rfq-ayar"
                  placeholder="14 / 18 / 22"
                  disabled={isBuyerRfqSubmitting}
                  {...registerBuyerRfq("hedef_ayar")}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-gram">Hedef gram</Label>
                <Input
                  id="rfq-gram"
                  className="font-mono tabular-nums text-right"
                  placeholder="35.50"
                  disabled={isBuyerRfqSubmitting}
                  {...registerBuyerRfq("hedef_gram")}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="rfq-qty">3. Adet</Label>
                <Input
                  id="rfq-qty"
                  className="font-mono tabular-nums text-right"
                  placeholder="5"
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
