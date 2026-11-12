"use client";

import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/features/auth";
import { useDocuments, useSubmitPodDocumentMutation } from "../hooks";
import { belgelerService } from "../services";
import { podAttachSchema, type PodAttachInput } from "../schemas";
import type { DocumentItem } from "../types";
import { formatDateTime } from "@/lib/format";
import { unwrapResults } from "@/lib/api/client";
import { useActionToast } from "@/hooks/use-action-toast";
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
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Download,
  RefreshCw,
  AlertCircle,
  FileText,
  Search,
  Eye,
  Plus,
  CheckCircle2,
  File,
  FileImage,
  ExternalLink,
  ArrowRight,
} from "lucide-react";

const PAGE_SIZE = 15;

const CATEGORIES = [
  { id: "all", label: "Tümü" },
  { id: "SEVKIYAT", label: "Sevkiyat" },
  { id: "POD", label: "POD" },
  { id: "SIPARIS", label: "Sipariş" },
  { id: "LEDGER", label: "Ledger / ödeme" },
  { id: "IADE", label: "İade" },
  { id: "KALITE", label: "Kalite" },
] as const;

function typeIcon(format?: string) {
  if (format === "IMAGE") return FileImage;
  if (format === "PDF" || format === "URL") return FileText;
  return File;
}

function statusVariant(
  durum?: string
): "success" | "warning" | "destructive" | "secondary" | "outline" {
  if (!durum) return "outline";
  const d = durum.toUpperCase();
  if (
    ["TESLIM_EDILDI", "TAMAMLANDI", "ONAYLANDI", "KAYITLI", "PASS", "GECTI"].some(
      (x) => d.includes(x)
    )
  ) {
    return "success";
  }
  if (["BEKLEMEDE", "YOLDA", "HAZIR", "OLCUMDE", "TASLAK"].some((x) => d.includes(x))) {
    return "warning";
  }
  if (["IPTAL", "RED", "FAIL", "REDDEDILDI"].some((x) => d.includes(x))) {
    return "destructive";
  }
  return "secondary";
}

export function DocumentsView() {
  const { user } = useAuth();
  const canPod = Boolean(
    user?.capabilities?.can_manage_shipment || user?.capabilities?.can_view_ops
  );

  const actionToast = useActionToast();
  const { documents, errors, loading, error, refresh } = useDocuments();
  const podMut = useSubmitPodDocumentMutation();

  const [q, setQ] = useState("");
  const [tip, setTip] = useState("all");
  const [durum, setDurum] = useState("all");
  const [kaynak, setKaynak] = useState("all");
  const [page, setPage] = useState(1);
  const [detail, setDetail] = useState<DocumentItem | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [podOpen, setPodOpen] = useState(false);
  const [shipOptions, setShipOptions] = useState<
    Array<{ id: number; durum: string; label: string }>
  >([]);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const {
    register: registerPod,
    handleSubmit: handlePodSubmit,
    reset: resetPod,
    formState: { errors: podErrors, isSubmitting: isPodSubmitting },
  } = useForm<PodAttachInput>({
    resolver: zodResolver(podAttachSchema),
    defaultValues: {
      shipment_id: 0,
      teslim_alan: "",
      notlar: "",
      belgeler_ref: "",
    },
  });

  const filtered = useMemo(() => {
    const qq = q.trim().toLowerCase();
    return documents.filter((d) => {
      if (tip !== "all" && d.belge_tipi !== tip) return false;
      if (durum !== "all" && (d.durum || "") !== durum) return false;
      if (kaynak !== "all" && d.referans_tipi !== kaynak) return false;
      if (!qq) return true;
      const blob = `${d.ad} ${d.belge_no || ""} ${d.raw_ref || ""} ${d.dosya_url || ""} ${d.referans_id}`.toLowerCase();
      return blob.includes(qq);
    });
  }, [documents, q, tip, durum, kaynak]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageRows = filtered.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

  const stats = useMemo(() => {
    const byTip = (t: string) => documents.filter((d) => d.belge_tipi === t).length;
    const pending = documents.filter((d) =>
      /BEKLEMEDE|TASLAK|HAZIR|YOLDA|OLCUMDE/i.test(d.durum || "")
    ).length;
    const approved = documents.filter((d) =>
      /ONAYLANDI|TESLIM|TAMAMLANDI|KAYITLI|PASS|GECTI/i.test(d.durum || "")
    ).length;
    const rejected = documents.filter((d) =>
      /RED|IPTAL|FAIL/i.test(d.durum || "")
    ).length;
    const downloadable = documents.filter((d) => Boolean(d.dosya_url)).length;
    return {
      total: documents.length,
      pending,
      approved,
      rejected,
      downloadable,
      pod: byTip("POD"),
      siparis: byTip("SIPARIS"),
      sevkiyat: byTip("SEVKIYAT"),
    };
  }, [documents]);

  const durumOptions = useMemo(() => {
    const set = new Set<string>();
    for (const d of documents) if (d.durum) set.add(d.durum);
    return [...set].sort();
  }, [documents]);

  const clearFilters = () => {
    setQ("");
    setTip("all");
    setDurum("all");
    setKaynak("all");
    setPage(1);
  };

  const openPodModal = async () => {
    setPodOpen(true);
    setActionError(null);
    try {
      const pageData = await belgelerService.listOpsShipments();
      const rows = unwrapResults(pageData);
      setShipOptions(
        rows.map((s) => ({
          id: s.id,
          durum: s.durum,
          label: `#${s.id} · ${s.durum}${s.order_id ? ` · sipariş ${s.order_id}` : ""}`,
        }))
      );
    } catch (err) {
      setShipOptions([]);
      setActionError(
        err instanceof Error ? err.message : "Ops sevkiyat listesi alınamadı."
      );
    }
  };

  const onPodSave = async (data: PodAttachInput) => {
    setActionError(null);
    try {
      await podMut.mutateAsync({
        shipment_id: data.shipment_id,
        teslim_alan: data.teslim_alan,
        notlar: data.notlar,
        belgeler_ref: data.belgeler_ref,
      });
      setPodOpen(false);
      resetPod();
      setSuccessMsg("POD kaydı oluşturuldu (belgeler_ref saklandı).");
      actionToast.success("POD kaydedildi");
      await refresh();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "POD kaydı başarısız.");
      actionToast.error("POD kaydı başarısız", err);
    }
  };

  const handleDownload = async (doc: DocumentItem) => {
    if (!doc.dosya_url) return;
    setActionError(null);
    setDownloading(true);
    try {
      const name = `${doc.belge_no || doc.id}`;
      await belgelerService.downloadUrl(doc.dosya_url, name);
      setSuccessMsg("İndirme başladı.");
    } catch (err) {
      // CORS / dış URL: yeni sekme
      try {
        window.open(doc.dosya_url, "_blank", "noopener,noreferrer");
      } catch {
        setActionError(
          err instanceof Error ? err.message : "İndirme başarısız."
        );
      }
    } finally {
      setDownloading(false);
    }
  };

  const previewable =
    detail?.dosya_url &&
    (detail.format === "PDF" ||
      detail.format === "IMAGE" ||
      detail.format === "URL");

  return (
    <div className="flex flex-col gap-6 max-w-[1100px]">
      <div className="flex flex-col gap-4 border-b border-border pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Belgeler
          </h1>
          <p className="text-xs text-muted-foreground max-w-[62ch] leading-relaxed">
            Ayrı `/belgeler/` endpoint’i yok. Liste sevkiyat/POD, sipariş, ledger,
            iade ve QC kayıtlarından yetkinize göre derlenir. Binary dosya
            yükleme API’si yoktur; POD için `belgeler_ref` (URL/anahtar) kullanılır.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => void refresh()}
            disabled={loading}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Yenile
          </Button>
          {canPod ? (
            <Button size="sm" className="gap-1.5" onClick={() => void openPodModal()}>
              <Plus className="h-3.5 w-3.5" />
              POD referansı
            </Button>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
        <Stat label="Toplam kayıt" value={String(stats.total)} />
        <Stat label="Bekleyen / süreçte" value={String(stats.pending)} />
        <Stat label="Tamamlanan" value={String(stats.approved)} />
        <Stat label="Red / iptal" value={String(stats.rejected)} />
        <Stat label="İndirilebilir URL" value={String(stats.downloadable)} />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => {
              setTip(c.id);
              setPage(1);
            }}
            className={`rounded-[6px] border px-2.5 py-1.5 text-xs font-medium transition-colors ${
              tip === c.id
                ? "border-border bg-secondary text-foreground"
                : "border-border bg-card text-muted-foreground hover:text-foreground"
            }`}
          >
            {c.label}
            {c.id !== "all"
              ? ` (${documents.filter((d) => d.belge_tipi === c.id).length})`
              : ` (${documents.length})`}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            placeholder="Ad, numara veya referans ara…"
            className="pl-8 h-9"
          />
        </div>
        <select
          value={durum}
          onChange={(e) => {
            setDurum(e.target.value);
            setPage(1);
          }}
          className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs"
        >
          <option value="all">Tüm durumlar</option>
          {durumOptions.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          value={kaynak}
          onChange={(e) => {
            setKaynak(e.target.value);
            setPage(1);
          }}
          className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs"
        >
          <option value="all">Tüm kaynaklar</option>
          <option value="shipment">Alıcı sevkiyat</option>
          <option value="ops_shipment">Ops sevkiyat</option>
          <option value="order">Sipariş</option>
          <option value="ledger">Ledger</option>
          <option value="return">İade</option>
          <option value="inspection">Kalite</option>
        </select>
        <Button variant="ghost" size="sm" className="h-9 text-xs" onClick={clearFilters}>
          Temizle
        </Button>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 rounded-[6px] border border-border bg-muted/60 p-3 text-xs font-medium">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMsg}</span>
          <button
            type="button"
            className="ml-auto text-muted-foreground"
            onClick={() => setSuccessMsg(null)}
          >
            Kapat
          </button>
        </div>
      )}

      {(error || actionError) && (
        <div
          className="flex items-center justify-between rounded-[8px] border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{actionError || error}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="h-8"
            onClick={() => {
              setActionError(null);
              void refresh();
            }}
          >
            Yeniden dene
          </Button>
        </div>
      )}

      {Object.keys(errors).length > 0 && documents.length > 0 ? (
        <p className="text-[11px] text-muted-foreground">
          Kısmi kaynak hataları:{" "}
          {Object.entries(errors)
            .map(([k, v]) => `${k}`)
            .join(", ")}
        </p>
      ) : null}

      {loading ? (
        <div className="flex h-48 items-center justify-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Belgeler derleniyor…
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-[8px] border border-border bg-card p-6 text-center">
          <FileText className="h-8 w-8 text-muted-foreground opacity-40" />
          <p className="text-sm font-medium text-foreground">
            {documents.length === 0
              ? "Belge kaydı bulunamadı"
              : "Arama sonucu yok"}
          </p>
          <p className="text-xs text-muted-foreground max-w-sm">
            Yetkili olduğunuz sevkiyat, sipariş, ledger, iade veya QC kaynağında
            satır yok; filtreleri temizleyin.
          </p>
        </div>
      ) : (
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10" />
                <TableHead>Belge</TableHead>
                <TableHead>No</TableHead>
                <TableHead>Tür</TableHead>
                <TableHead>İlişki</TableHead>
                <TableHead>Durum</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Tarih</TableHead>
                <TableHead className="text-right">İşlem</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageRows.map((d) => {
                const Icon = typeIcon(d.format);
                return (
                  <TableRow key={d.id}>
                    <TableCell>
                      <Icon className="h-4 w-4 text-muted-foreground" />
                    </TableCell>
                    <TableCell className="font-medium text-xs">{d.ad}</TableCell>
                    <TableCell className="font-mono text-[11px]">
                      {d.belge_no || "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px]">
                        {d.belge_tipi}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-[11px] text-muted-foreground">
                      {d.referans_tipi} #{d.referans_id}
                      {d.related_order_id != null
                        ? ` · ORD ${d.related_order_id}`
                        : ""}
                    </TableCell>
                    <TableCell>
                      {d.durum ? (
                        <Badge
                          variant={statusVariant(d.durum)}
                          className="font-mono text-[10px]"
                        >
                          {d.durum}
                        </Badge>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-[10px] text-muted-foreground">
                      {d.format || "—"}
                    </TableCell>
                    <TableCell className="text-[11px] text-muted-foreground">
                      {d.olusturma_tarihi
                        ? formatDateTime(d.olusturma_tarihi)
                        : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs gap-1"
                          onClick={() => setDetail(d)}
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Detay
                        </Button>
                        {d.dosya_url ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 text-xs gap-1"
                            disabled={downloading}
                            onClick={() => void handleDownload(d)}
                          >
                            <Download className="h-3.5 w-3.5" />
                            İndir
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted-foreground">
            <span>
              {filtered.length} kayıt · sayfa {safePage}/{totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8"
                disabled={safePage <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Önceki
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-8"
                disabled={safePage >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Sonraki
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Detail */}
      <Dialog open={Boolean(detail)} onOpenChange={(o) => !o && setDetail(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{detail?.ad || "Belge detayı"}</DialogTitle>
            <DialogDescription className="font-mono text-xs">
              {detail?.belge_no} · {detail?.referans_tipi} #{detail?.referans_id}
            </DialogDescription>
          </DialogHeader>
          {detail ? (
            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <Info label="Tür" value={detail.belge_tipi} />
                <Info label="Durum" value={detail.durum || "—"} />
                <Info label="Format" value={detail.format || "—"} />
                <Info
                  label="Tarih"
                  value={
                    detail.olusturma_tarihi
                      ? formatDateTime(detail.olusturma_tarihi)
                      : "—"
                  }
                />
                <Info
                  label="İlişkili sipariş"
                  value={
                    detail.related_order_id != null
                      ? `#${detail.related_order_id}`
                      : "—"
                  }
                  mono
                />
                <Info
                  label="Referans"
                  value={detail.raw_ref || "—"}
                  mono
                />
              </div>
              {detail.dosya_url ? (
                <div className="rounded-[6px] border border-border px-3 py-2 break-all">
                  <div className="text-[10px] text-muted-foreground">Dosya URL</div>
                  <a
                    href={detail.dosya_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-[11px] text-foreground hover:underline inline-flex items-center gap-1"
                  >
                    {detail.dosya_url}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              ) : null}
              {detail.meta && Object.keys(detail.meta).length > 0 ? (
                <div className="rounded-[6px] border border-border px-3 py-2 space-y-1">
                  <div className="text-[10px] text-muted-foreground">Ek alanlar</div>
                  {Object.entries(detail.meta).map(([k, v]) =>
                    v == null || v === "" ? null : (
                      <div key={k} className="flex justify-between gap-2">
                        <span className="text-muted-foreground">{k}</span>
                        <span className="font-mono text-right">{String(v)}</span>
                      </div>
                    )
                  )}
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2 border-t border-border pt-3">
                {detail.dosya_url ? (
                  <>
                    <Button
                      size="sm"
                      className="h-8 text-xs gap-1"
                      disabled={downloading}
                      onClick={() => void handleDownload(detail)}
                    >
                      <Download className="h-3.5 w-3.5" />
                      İndir
                    </Button>
                    {previewable ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-xs gap-1"
                        onClick={() => setPreviewOpen(true)}
                      >
                        <Eye className="h-3.5 w-3.5" />
                        Önizle
                      </Button>
                    ) : null}
                  </>
                ) : null}
                {detail.href ? (
                  <Button size="sm" variant="outline" className="h-8 text-xs gap-1" asChild>
                    <Link to={detail.href}>
                      İlgili modül
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Preview */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Önizleme</DialogTitle>
            <DialogDescription>{detail?.ad}</DialogDescription>
          </DialogHeader>
          {detail?.dosya_url ? (
            detail.format === "IMAGE" ? (
              <img
                src={detail.dosya_url}
                alt={detail.ad}
                className="max-h-[70vh] w-full object-contain rounded-[6px] border border-border"
              />
            ) : (
              <iframe
                title={detail.ad}
                src={detail.dosya_url}
                className="h-[70vh] w-full rounded-[6px] border border-border bg-background"
              />
            )
          ) : (
            <p className="text-xs text-muted-foreground">Önizlenebilir URL yok.</p>
          )}
        </DialogContent>
      </Dialog>

      {/* POD attach — not multipart file API */}
      <Dialog open={podOpen} onOpenChange={setPodOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>POD belge referansı</DialogTitle>
            <DialogDescription>
              `POST /ops/shipments/{"{id}"}/pod/` — binary upload yok; `belgeler_ref`
              harici anahtar veya URL (max 255).
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={handlePodSubmit(onPodSave)}
            className="flex flex-col gap-3 pt-1"
          >
            <div className="flex flex-col gap-1.5">
              <Label>Sevkiyat</Label>
              <select
                className="h-9 w-full rounded-[6px] border border-border bg-background px-2 text-xs"
                disabled={isPodSubmitting}
                {...registerPod("shipment_id", { valueAsNumber: true })}
              >
                <option value={0}>Seçin…</option>
                {shipOptions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
              {podErrors.shipment_id ? (
                <span className="text-[11px] text-destructive">
                  {podErrors.shipment_id.message}
                </span>
              ) : null}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Teslim alan</Label>
              <Input
                disabled={isPodSubmitting}
                {...registerPod("teslim_alan")}
              />
              {podErrors.teslim_alan ? (
                <span className="text-[11px] text-destructive">
                  {podErrors.teslim_alan.message}
                </span>
              ) : null}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>belgeler_ref (URL veya anahtar)</Label>
              <Input
                className="font-mono text-xs"
                placeholder="https://… veya storage-key"
                disabled={isPodSubmitting}
                {...registerPod("belgeler_ref")}
              />
              {podErrors.belgeler_ref ? (
                <span className="text-[11px] text-destructive">
                  {podErrors.belgeler_ref.message}
                </span>
              ) : null}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Notlar</Label>
              <Input disabled={isPodSubmitting} {...registerPod("notlar")} />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPodOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isPodSubmitting}>
                {isPodSubmitting ? "Kaydediliyor…" : "POD kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[8px] border border-border bg-card p-4 space-y-1">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="text-xl font-semibold font-mono tabular-nums">{value}</div>
    </div>
  );
}

function Info({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-[6px] border border-border px-2.5 py-2">
      <div className="text-[10px] text-muted-foreground">{label}</div>
      <div className={`text-xs break-all ${mono ? "font-mono" : "font-medium"}`}>
        {value}
      </div>
    </div>
  );
}
