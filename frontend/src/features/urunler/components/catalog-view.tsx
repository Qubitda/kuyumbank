"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/features/auth";
import { urunlerService } from "../services";
import {
  useCatalogQuery,
  useOpsProductsQuery,
  useCreateOpsProductMutation,
  useOpsProductActionMutation,
  urunlerKeys,
} from "../hooks";
import { useQueryClient } from "@tanstack/react-query";
import { useActionToast } from "@/hooks/use-action-toast";
import { useUrlState } from "@/lib/hooks/use-url-state";
import {
  opsProductCreateSchema,
  opsVariantCreateSchema,
  rejectSchema,
  type OpsProductCreateInput,
  type OpsVariantCreateInput,
  type RejectInput,
} from "../schemas";
import type {
  BuyerCatalogDetail,
  BuyerCatalogItem,
  OpsProduct,
} from "../types";
import { fiyatlamaService, rememberQuoteId } from "@/features/fiyatlama";
import { siparisService } from "@/features/siparis";
import { tanimlarService } from "@/features/tanimlar";
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
  Search,
  Eye,
  AlertCircle,
  RefreshCw,
  Gem,
  Tag,
  ShoppingCart,
  Check,
  Scale,
  LayoutGrid,
  List,
  Plus,
  CheckCircle2,
  Boxes,
} from "lucide-react";
import { VariantCompareModal } from "./variant-compare-modal";

type ViewMode = "table" | "cards";
type Scope = "buyer" | "ops";
type DetailTab = "general" | "tech" | "variants" | "commerce" | "images";

const PAGE_SIZE = 20;

export function CatalogView() {
  const { id: routeId } = useParams<{ id?: string }>();
  const { user } = useAuth();
  const actionToast = useActionToast();
  const queryClient = useQueryClient();
  const canOps = Boolean(user?.capabilities?.can_view_ops && user?.firma?.platform_mu);
  const canCatalog = Boolean(user?.capabilities?.can_view_catalog || canOps);
  const canQuote = Boolean(user?.capabilities?.can_lock_quote || user?.capabilities?.can_view_cart);
  const canStock = Boolean(user?.capabilities?.can_view_supplier_stock);

  const { get, setMany, page } = useUrlState();
  const scopeParam = get("scope");
  const scope: Scope =
    scopeParam === "ops" && canOps
      ? "ops"
      : scopeParam === "buyer"
        ? "buyer"
        : canOps
          ? "ops"
          : "buyer";
  const setScope = (next: Scope) =>
    setMany({
      scope: next,
      page: 1,
      onay: undefined,
      yayin: undefined,
    });

  const [viewMode, setViewMode] = useState<ViewMode>("table");

  const q = get("q");
  const ordering = get("ordering", scope === "ops" ? "-pk" : "pk") || "pk";
  const onayDurumu = get("onay");
  const yayinDurumu = get("yayin");
  const [qInput, setQInput] = useState(q);

  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const createOpsMutation = useCreateOpsProductMutation();
  const opsActionMutation = useOpsProductActionMutation();

  const [detailOpen, setDetailOpen] = useState(false);
  const [detailTab, setDetailTab] = useState<DetailTab>("general");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [buyerDetail, setBuyerDetail] = useState<BuyerCatalogDetail | null>(null);
  const [opsDetail, setOpsDetail] = useState<OpsProduct | null>(null);

  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);
  const [compareModalOpen, setCompareModalOpen] = useState(false);

  const [createOpen, setCreateOpen] = useState(false);
  const [variantOpen, setVariantOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [channels, setChannels] = useState<Array<{ id: number; ad?: string }>>([]);

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

  useEffect(() => {
    if (!canOps && scope === "ops") setScope("buyer");
  }, [canOps, scope]);

  useEffect(() => {
    setQInput(q);
  }, [q]);

  // Debounce search → URL
  useEffect(() => {
    const t = window.setTimeout(() => {
      const next = qInput.trim();
      if (next === q) return;
      setMany({ q: next || undefined, page: 1 });
    }, 350);
    return () => window.clearTimeout(t);
  }, [qInput, q, setMany]);

  const catalogFilters = useMemo(
    () => ({
      q: q || undefined,
      ordering: ordering || undefined,
      page: String(page),
      page_size: String(PAGE_SIZE),
    }),
    [q, ordering, page]
  );

  const opsFilters = useMemo(
    () => ({
      ...catalogFilters,
      onay_durumu: onayDurumu || undefined,
      yayin_durumu: yayinDurumu || undefined,
    }),
    [catalogFilters, onayDurumu, yayinDurumu]
  );

  const catalogQuery = useCatalogQuery(
    catalogFilters,
    scope === "buyer" && (canCatalog || canOps)
  );
  const opsQuery = useOpsProductsQuery(opsFilters, scope === "ops" && canOps);

  const buyerItems = catalogQuery.data?.results || [];
  const opsItems = opsQuery.data?.results || [];
  const totalCount =
    scope === "ops"
      ? opsQuery.data?.count ?? 0
      : catalogQuery.data?.count ?? 0;
  const pageSize =
    (scope === "ops"
      ? opsQuery.data?.page_size
      : catalogQuery.data?.page_size) || PAGE_SIZE;
  const loading =
    (scope === "ops" ? opsQuery.isLoading : catalogQuery.isLoading) ||
    (scope === "ops" ? opsQuery.isFetching : catalogQuery.isFetching);
  const listError =
    scope === "ops"
      ? opsQuery.error
      : catalogQuery.error;
  const fetchList = useCallback(async () => {
    setError(null);
    await queryClient.invalidateQueries({ queryKey: urunlerKeys.all });
  }, [queryClient]);

  useEffect(() => {
    if (listError) {
      setError(
        listError instanceof Error ? listError.message : "Katalog alınamadı."
      );
    }
  }, [listError]);

  useEffect(() => {
    if (!routeId) return;
    const n = Number(routeId);
    if (!Number.isFinite(n) || n <= 0) return;
    if (scope === "ops" && canOps) void openOpsDetail(n);
    else void openBuyerDetail(n);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- deep-link once per id/scope
  }, [routeId, scope, canOps]);

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  const stats = useMemo(() => {
    if (scope === "ops") {
      const aktif = opsItems.filter((i) => i.yayin_durumu === "aktif").length;
      const pasif = opsItems.filter((i) => i.yayin_durumu !== "aktif").length;
      const cats = new Set(opsItems.map((i) => i.kategori).filter(Boolean)).size;
      return { total: totalCount, aktif, pasif, cats, pageNote: true };
    }
    const aktif = buyerItems.filter(
      (i) => !i.yayin_durumu || i.yayin_durumu === "aktif"
    ).length;
    const cats = new Set(buyerItems.map((i) => i.kategori).filter(Boolean)).size;
    return {
      total: totalCount,
      aktif: totalCount,
      pasif: 0,
      cats,
      pageNote: true,
    };
  }, [scope, opsItems, buyerItems, totalCount]);

  const clearFilters = () => {
    setQInput("");
    setMany({
      q: undefined,
      ordering: scope === "ops" ? "-pk" : "pk",
      onay: undefined,
      yayin: undefined,
      page: 1,
    });
  };

  const openBuyerDetail = async (id: number) => {
    setDetailOpen(true);
    setDetailTab("general");
    setLoadingDetail(true);
    setBuyerDetail(null);
    setOpsDetail(null);
    try {
      const d = await urunlerService.getProductDetail(id);
      setBuyerDetail(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ürün detayı alınamadı.");
      setDetailOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const openOpsDetail = async (id: number) => {
    setDetailOpen(true);
    setDetailTab("general");
    setLoadingDetail(true);
    setBuyerDetail(null);
    setOpsDetail(null);
    try {
      const d = await urunlerService.getOpsProduct(id);
      setOpsDetail(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ürün detayı alınamadı.");
      setDetailOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleGetQuote = async (variantId: number) => {
    setQuoteState((prev) => ({ ...prev, [variantId]: { loading: true } }));
    try {
      const list = await tanimlarService.getSalesChannels();
      const channelId = list[0]?.id;
      if (!channelId) throw new Error("Satış kanalı bulunamadı.");
      const quote = await fiyatlamaService.createQuote({
        varyant_id: variantId,
        satis_kanali_id: channelId,
      });
      const price = quote.toplam_vergisiz || quote.gram_basi_vergisiz || quote.birim_fiyat;
      if (!price) throw new Error("Backend fiyat alanı dönmedi.");
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
      setSuccessMsg("Sepete eklendi.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sepete eklenemedi.");
    }
  };

  const {
    register: registerCreate,
    handleSubmit: handleCreateSubmit,
    reset: resetCreate,
    formState: { errors: createErrors, isSubmitting: isCreating },
  } = useForm<OpsProductCreateInput>({
    resolver: zodResolver(opsProductCreateSchema),
    defaultValues: {
      ad: "",
      kategori_id: 0,
      ayar_id: 0,
      aciklama: "",
      fiyat_tipi: "gram",
    },
  });

  const {
    register: registerVariant,
    handleSubmit: handleVariantSubmit,
    reset: resetVariant,
    formState: { errors: variantErrors, isSubmitting: isVariantSubmitting },
  } = useForm<OpsVariantCreateInput>({
    resolver: zodResolver(opsVariantCreateSchema),
    defaultValues: { gram: "", ek_bedel: "" },
  });

  const {
    register: registerReject,
    handleSubmit: handleRejectSubmit,
    reset: resetReject,
    formState: { errors: rejectErrors, isSubmitting: isRejecting },
  } = useForm<RejectInput>({
    resolver: zodResolver(rejectSchema),
    defaultValues: { neden: "" },
  });

  const openCreate = async () => {
    setCreateOpen(true);
    try {
      const ch = await tanimlarService.getSalesChannels();
      setChannels(ch.map((c) => ({ id: c.id, ad: c.ad })));
    } catch {
      setChannels([]);
    }
  };

  const onCreate = async (data: OpsProductCreateInput) => {
    setError(null);
    try {
      const body = {
        ad: data.ad,
        kategori_id: data.kategori_id,
        ayar_id: data.ayar_id,
        aciklama: data.aciklama || "",
        fiyat_tipi: data.fiyat_tipi || "gram",
        ...(data.satis_kanali_id ? { satis_kanali_id: data.satis_kanali_id } : {}),
      };
      const created = await createOpsMutation.mutateAsync(body);
      setCreateOpen(false);
      resetCreate();
      setSuccessMsg(`Taslak ürün #${created.id} oluşturuldu.`);
      actionToast.success("Ürün oluşturuldu", `#${created.id}`);
      await openOpsDetail(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ürün oluşturulamadı.");
      actionToast.error("Ürün oluşturulamadı", err);
    }
  };

  const onAddVariant = async (data: OpsVariantCreateInput) => {
    if (!opsDetail) return;
    setError(null);
    try {
      await opsActionMutation.mutateAsync({
        action: "addVariant",
        id: opsDetail.id,
        variant: {
          gram: data.gram || undefined,
          renk_id: data.renk_id,
          ek_bedel: data.ek_bedel || undefined,
        },
      });
      setVariantOpen(false);
      resetVariant();
      setSuccessMsg("Varyant eklendi.");
      actionToast.success("Varyant eklendi");
      await openOpsDetail(opsDetail.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Varyant eklenemedi.");
      actionToast.error("Varyant eklenemedi", err);
    }
  };

  const runOpsAction = async (
    action: "submit" | "approve" | "publish" | "unpublish",
    id: number
  ) => {
    setError(null);
    try {
      await opsActionMutation.mutateAsync({
        action,
        id,
        durum: action === "publish" ? "aktif" : undefined,
      });
      setSuccessMsg(`İşlem tamamlandı: ${action}`);
      actionToast.success("İşlem tamamlandı", action);
      if (opsDetail?.id === id) await openOpsDetail(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "İşlem başarısız.");
      actionToast.error("İşlem başarısız", err);
    }
  };

  const onReject = async (data: RejectInput) => {
    if (!opsDetail) return;
    try {
      await opsActionMutation.mutateAsync({
        action: "reject",
        id: opsDetail.id,
        neden: data.neden,
      });
      setRejectOpen(false);
      resetReject();
      setSuccessMsg("Ürün reddedildi.");
      actionToast.success("Ürün reddedildi");
      await openOpsDetail(opsDetail.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reddetme başarısız.");
      actionToast.error("Reddetme başarısız", err);
    }
  };

  const toggleCompare = (id: number) => {
    setSelectedForCompare((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : prev.length < 4
          ? [...prev, id]
          : prev
    );
  };

  const activeDetail = opsDetail || buyerDetail;
  const actions = opsDetail?.allowed_actions || [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 border-b border-border pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Ürün Kataloğu
          </h1>
          <p className="text-xs text-muted-foreground max-w-[60ch]">
            Platform onaylı yayınlı ürünler (alıcı) ve ops taslak/onay akışı.
            Fiyat quote ile alınır; görsel/barkod/marka alanları API’de yok.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {canOps ? (
            <div className="flex rounded-[6px] border border-border bg-muted/40 p-1">
              <button
                type="button"
                className={`rounded-[4px] px-2.5 py-1.5 text-xs font-medium ${
                  scope === "buyer" ? "bg-card shadow-xs" : "text-muted-foreground"
                }`}
                onClick={() => {
                  setMany({ scope: "buyer", page: 1, ordering: "pk", onay: undefined, yayin: undefined });
                }}
              >
                Alıcı katalog
              </button>
              <button
                type="button"
                className={`rounded-[4px] px-2.5 py-1.5 text-xs font-medium ${
                  scope === "ops" ? "bg-card shadow-xs" : "text-muted-foreground"
                }`}
                onClick={() => {
                  setMany({ scope: "ops", page: 1, ordering: "-pk" });
                }}
              >
                Ops ürünler
              </button>
            </div>
          ) : null}
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => void fetchList()}
            disabled={loading}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Yenile
          </Button>
          {scope === "ops" && canOps ? (
            <Button size="sm" className="gap-1.5" onClick={() => void openCreate()}>
              <Plus className="h-3.5 w-3.5" />
              Yeni ürün
            </Button>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Toplam ürün" value={String(stats.total)} />
        <Stat
          label={scope === "ops" ? "Aktif (sayfa)" : "Yayınlı (toplam)"}
          value={String(stats.aktif)}
        />
        <Stat
          label={scope === "ops" ? "Pasif (sayfa)" : "Pasif"}
          value={String(stats.pasif)}
        />
        <Stat label="Kategori (sayfa)" value={String(stats.cats)} />
      </div>

      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={qInput}
              onChange={(e) => setQInput(e.target.value)}
              placeholder="Ad veya platform kodu ara…"
              className="pl-8 h-9"
            />
          </div>
          <select
            value={ordering}
            onChange={(e) => {
              setMany({ ordering: e.target.value, page: 1 });
            }}
            className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs"
          >
            <option value="pk">Sıra: id ↑</option>
            <option value="-pk">Sıra: id ↓</option>
            <option value="ad">Sıra: ad ↑</option>
            <option value="-ad">Sıra: ad ↓</option>
            <option value="platform_kodu">Sıra: kod ↑</option>
            <option value="-platform_kodu">Sıra: kod ↓</option>
          </select>
          {scope === "ops" ? (
            <>
              <select
                value={onayDurumu}
                onChange={(e) => {
                  setMany({ onay: e.target.value || undefined, page: 1 });
                }}
                className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs"
              >
                <option value="">Tüm onay</option>
                <option value="taslak">taslak</option>
                <option value="onay_bekliyor">onay_bekliyor</option>
                <option value="onayli">onayli</option>
                <option value="reddedildi">reddedildi</option>
              </select>
              <select
                value={yayinDurumu}
                onChange={(e) => {
                  setMany({ yayin: e.target.value || undefined, page: 1 });
                }}
                className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs"
              >
                <option value="">Tüm yayın</option>
                <option value="aktif">aktif</option>
                <option value="pasif">pasif</option>
                <option value="yakinda">yakinda</option>
              </select>
            </>
          ) : null}
          <Button variant="ghost" size="sm" className="h-9 text-xs" onClick={clearFilters}>
            Filtreleri temizle
          </Button>
        </div>
        <div className="flex rounded-[6px] border border-border p-1 w-fit">
          <button
            type="button"
            className={`rounded-[4px] p-1.5 ${viewMode === "table" ? "bg-secondary" : ""}`}
            onClick={() => setViewMode("table")}
            aria-label="Tablo"
          >
            <List className="h-4 w-4" />
          </button>
          <button
            type="button"
            className={`rounded-[4px] p-1.5 ${viewMode === "cards" ? "bg-secondary" : ""}`}
            onClick={() => setViewMode("cards")}
            aria-label="Kartlar"
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 rounded-[6px] border border-border bg-muted/60 p-3 text-xs font-medium">
          <CheckCircle2 className="h-4 w-4" />
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

      {error && (
        <div
          className="flex items-center justify-between rounded-[8px] border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" className="h-8" onClick={() => void fetchList()}>
            Yeniden dene
          </Button>
        </div>
      )}

      {!canCatalog && !canOps ? (
        <p className="text-xs text-muted-foreground">Katalog yetkisi yok.</p>
      ) : loading ? (
        <div className="flex h-48 items-center justify-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Katalog yükleniyor…
        </div>
      ) : (scope === "buyer" ? buyerItems : opsItems).length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-[8px] border border-border bg-card p-6 text-center">
          <Gem className="h-8 w-8 text-muted-foreground opacity-50" />
          <p className="text-sm font-medium">
            {q || onayDurumu || yayinDurumu
              ? "Arama sonucu bulunamadı"
              : "Katalogda ürün yok"}
          </p>
          <p className="text-xs text-muted-foreground">
            Filtreleri temizleyin veya ops ile taslak ürün oluşturun.
          </p>
        </div>
      ) : viewMode === "table" ? (
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                {scope === "buyer" ? <TableHead className="w-10" /> : null}
                <TableHead>Kod</TableHead>
                <TableHead>Ürün</TableHead>
                <TableHead>Kategori</TableHead>
                <TableHead>Ayar</TableHead>
                <TableHead className="text-right">Varyant</TableHead>
                <TableHead>Fiyat tipi</TableHead>
                <TableHead>Durum</TableHead>
                <TableHead className="text-right">İşlem</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scope === "buyer"
                ? buyerItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={selectedForCompare.includes(item.id)}
                          onChange={() => toggleCompare(item.id)}
                          className="h-4 w-4 rounded-[4px] border-border"
                          aria-label="Karşılaştır"
                        />
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {item.platform_kodu || "—"}
                      </TableCell>
                      <TableCell className="font-medium">{item.ad}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {item.kategori || "—"}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {item.ayar || "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {item.varyant_count}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {item.fiyat_tipi || "—"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="success" className="font-mono text-[10px]">
                          {item.yayin_durumu || "aktif"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs gap-1"
                          onClick={() => void openBuyerDetail(item.id)}
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Detay
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                : opsItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-mono text-xs">
                        {item.platform_kodu || "—"}
                      </TableCell>
                      <TableCell className="font-medium">{item.ad}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {item.kategori || `#${item.kategori_id}`}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {item.ayar || `#${item.ayar_id}`}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {item.varyant_count}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {item.fiyat_tipi || "—"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-0.5">
                          <Badge variant="secondary" className="font-mono text-[10px] w-fit">
                            {item.onay_durumu}
                          </Badge>
                          <Badge
                            variant={
                              item.yayin_durumu === "aktif" ? "success" : "outline"
                            }
                            className="font-mono text-[10px] w-fit"
                          >
                            {item.yayin_durumu}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs gap-1"
                          onClick={() => void openOpsDetail(item.id)}
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Yönet
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(scope === "buyer" ? buyerItems : opsItems).map((item) => {
            const isBuyer = scope === "buyer";
            const buyer = item as BuyerCatalogItem;
            const ops = item as OpsProduct;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() =>
                  void (isBuyer ? openBuyerDetail(item.id) : openOpsDetail(item.id))
                }
                className="rounded-[8px] border border-border bg-card p-4 text-left hover:bg-muted/40 transition-colors space-y-3"
              >
                <div className="flex h-24 items-center justify-center rounded-[6px] border border-dashed border-border bg-muted/30">
                  <Gem className="h-8 w-8 text-muted-foreground opacity-40" />
                </div>
                <div>
                  <div className="font-mono text-[10px] text-muted-foreground">
                    {isBuyer ? buyer.platform_kodu : ops.platform_kodu || "—"}
                  </div>
                  <div className="text-sm font-semibold line-clamp-2">{item.ad}</div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {isBuyer ? buyer.kategori || "—" : ops.kategori || "—"}
                  </Badge>
                  <Badge variant="secondary" className="font-mono text-[10px]">
                    {isBuyer
                      ? `${buyer.varyant_count} varyant`
                      : `${ops.varyant_count} varyant`}
                  </Badge>
                  {!isBuyer ? (
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {ops.onay_durumu}
                    </Badge>
                  ) : null}
                </div>
              </button>
            );
          })}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {totalCount} kayıt · sayfa {page}/{totalPages}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-8"
            disabled={page <= 1}
            onClick={() => setMany({ page: Math.max(1, page - 1) })}
          >
            Önceki
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8"
            disabled={page >= totalPages}
            onClick={() => setMany({ page: page + 1 })}
          >
            Sonraki
          </Button>
        </div>
      </div>

      {/* Detail */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{activeDetail?.ad || "Ürün detayı"}</DialogTitle>
            <DialogDescription className="font-mono text-xs">
              {buyerDetail?.platform_kodu || opsDetail?.platform_kodu || "—"}
            </DialogDescription>
          </DialogHeader>

          {loadingDetail ? (
            <div className="flex h-32 items-center justify-center">
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          ) : activeDetail ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-1 rounded-[6px] border border-border bg-muted/40 p-1 w-fit">
                {(
                  [
                    ["general", "Genel"],
                    ["tech", "Teknik"],
                    ["variants", "Varyantlar"],
                    ["commerce", "Ticari"],
                    ["images", "Görseller"],
                  ] as const
                ).map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setDetailTab(id)}
                    className={`rounded-[4px] px-2.5 py-1.5 text-xs font-medium ${
                      detailTab === id
                        ? "bg-card shadow-xs"
                        : "text-muted-foreground"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {detailTab === "general" && (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <Info label="Ad" value={activeDetail.ad} />
                  <Info
                    label="Platform kodu"
                    value={
                      buyerDetail?.platform_kodu ||
                      opsDetail?.platform_kodu ||
                      "—"
                    }
                    mono
                  />
                  <Info
                    label="Kategori"
                    value={
                      buyerDetail?.kategori ||
                      opsDetail?.kategori ||
                      (opsDetail ? `#${opsDetail.kategori_id}` : "—")
                    }
                  />
                  <Info
                    label="Ayar"
                    value={
                      buyerDetail?.ayar ||
                      opsDetail?.ayar ||
                      (opsDetail ? `#${opsDetail.ayar_id}` : "—")
                    }
                    mono
                  />
                  {opsDetail ? (
                    <>
                      <Info label="Onay" value={opsDetail.onay_durumu} mono />
                      <Info label="Yayın" value={opsDetail.yayin_durumu} mono />
                      {opsDetail.red_nedeni ? (
                        <Info label="Red nedeni" value={opsDetail.red_nedeni} />
                      ) : null}
                    </>
                  ) : (
                    <Info label="Yayın" value="aktif (katalog)" mono />
                  )}
                  <div className="col-span-2 rounded-[6px] border border-border px-3 py-2">
                    <div className="text-[10px] text-muted-foreground">Açıklama</div>
                    <p className="text-xs mt-1">
                      {buyerDetail?.aciklama || opsDetail?.aciklama || "—"}
                    </p>
                  </div>
                </div>
              )}

              {detailTab === "tech" && (
                <div className="space-y-2 text-xs">
                  <Info
                    label="Fiyat tipi"
                    value={
                      buyerDetail?.fiyat_tipi || opsDetail?.fiyat_tipi || "—"
                    }
                    mono
                  />
                  <Info label="Ayar / milyem" value={buyerDetail?.ayar || opsDetail?.ayar || "—"} mono />
                  <p className="text-[11px] text-muted-foreground">
                    Ölçü, malzeme, ağırlık özeti API şemasında ürün seviyesinde
                    yok; gram varyant satırındadır.
                  </p>
                </div>
              )}

              {detailTab === "images" && (
                <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-[6px] border border-dashed border-border text-xs text-muted-foreground">
                  <Gem className="h-8 w-8 opacity-40" />
                  Ürün görseli endpoint’i yok — sahte görsel kullanılmaz.
                </div>
              )}

              {detailTab === "commerce" && (
                <div className="space-y-3 text-xs">
                  <Info
                    label="Fiyat tipi"
                    value={
                      buyerDetail?.fiyat_tipi || opsDetail?.fiyat_tipi || "—"
                    }
                    mono
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Sabit satış/alış fiyatı katalogda yok. Alıcı fiyatı quote ile
                    alınır; maliyet/marj/tedarikçi alanları kör havuzda
                    gizlidir (yalnız net toplam / gram başı).
                  </p>
                  {canStock ? (
                    <Link
                      to="/stok"
                      className="inline-flex items-center gap-1.5 text-xs font-medium hover:underline"
                    >
                      <Boxes className="h-3.5 w-3.5" />
                      Stok ekranına git
                    </Link>
                  ) : null}
                </div>
              )}

              {detailTab === "variants" && (
                <div className="space-y-3">
                  {opsDetail && actions.includes("add_variant") ? (
                    <div className="flex justify-end">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-xs"
                        onClick={() => setVariantOpen(true)}
                      >
                        Varyant ekle
                      </Button>
                    </div>
                  ) : null}

                  {buyerDetail ? (
                    buyerDetail.varyantlar?.length ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>SKU</TableHead>
                            <TableHead>Beden</TableHead>
                            <TableHead>Renk</TableHead>
                            <TableHead className="text-right">Gram</TableHead>
                            <TableHead className="text-right">Fiyat / Sepet</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {buyerDetail.varyantlar.map((v) => {
                            const st = quoteState[v.id];
                            return (
                              <TableRow key={v.id}>
                                <TableCell className="font-mono text-xs">
                                  {v.sku}
                                </TableCell>
                                <TableCell className="text-xs">
                                  {v.beden || "—"}
                                </TableCell>
                                <TableCell className="text-xs">
                                  {v.renk || "—"}
                                </TableCell>
                                <TableCell className="text-right font-mono tabular-nums text-xs">
                                  {formatGram(v.gram)}
                                </TableCell>
                                <TableCell className="text-right">
                                  {!canQuote ? (
                                    <span className="text-[11px] text-muted-foreground">
                                      —
                                    </span>
                                  ) : !st?.price ? (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      className="h-7 text-xs gap-1"
                                      disabled={st?.loading}
                                      onClick={() => void handleGetQuote(v.id)}
                                    >
                                      <Tag className="h-3 w-3" />
                                      {st?.loading ? "…" : "Quote"}
                                    </Button>
                                  ) : st.added ? (
                                    <Badge
                                      variant="success"
                                      className="font-mono text-[10px] gap-1"
                                    >
                                      <Check className="h-3 w-3" />
                                      Sepette
                                    </Badge>
                                  ) : (
                                    <div className="flex items-center justify-end gap-2">
                                      <span className="font-mono text-xs tabular-nums font-semibold">
                                        {formatMoney(
                                          st.price,
                                          st.currency || "TRY"
                                        )}
                                      </span>
                                      <Button
                                        size="sm"
                                        className="h-7 text-xs gap-1"
                                        onClick={() =>
                                          void handleAddToCart(v.id, st.quoteId!)
                                        }
                                      >
                                        <ShoppingCart className="h-3 w-3" />
                                        Sepet
                                      </Button>
                                    </div>
                                  )}
                                  {st?.error ? (
                                    <div className="text-[10px] text-destructive mt-1">
                                      {st.error}
                                    </div>
                                  ) : null}
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    ) : (
                      <p className="text-xs text-muted-foreground">Varyant yok.</p>
                    )
                  ) : opsDetail?.varyantlar?.length ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>SKU</TableHead>
                          <TableHead>renk_id</TableHead>
                          <TableHead className="text-right">Gram</TableHead>
                          <TableHead className="text-right">Ek bedel</TableHead>
                          <TableHead>Durum</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {opsDetail.varyantlar.map((v) => (
                          <TableRow key={v.id}>
                            <TableCell className="font-mono text-xs">
                              {v.sku}
                            </TableCell>
                            <TableCell className="font-mono text-xs">
                              {v.renk_id ?? "—"}
                            </TableCell>
                            <TableCell className="text-right font-mono tabular-nums text-xs">
                              {formatGram(v.gram)}
                            </TableCell>
                            <TableCell className="text-right font-mono tabular-nums text-xs">
                              {v.ek_bedel ?? "—"}
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={v.aktif ? "success" : "secondary"}
                                className="font-mono text-[10px]"
                              >
                                {v.aktif ? "AKTİF" : "PASİF"}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <p className="text-xs text-muted-foreground">Varyant yok.</p>
                  )}
                </div>
              )}

              {opsDetail ? (
                <div className="flex flex-wrap gap-2 border-t border-border pt-3">
                  {actions.includes("submit") && (
                    <Button
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => void runOpsAction("submit", opsDetail.id)}
                    >
                      Onaya gönder
                    </Button>
                  )}
                  {actions.includes("approve") && (
                    <Button
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => void runOpsAction("approve", opsDetail.id)}
                    >
                      Onayla
                    </Button>
                  )}
                  {actions.includes("reject") && (
                    <Button
                      size="sm"
                      variant="destructive"
                      className="h-8 text-xs"
                      onClick={() => setRejectOpen(true)}
                    >
                      Reddet
                    </Button>
                  )}
                  {actions.includes("publish") && (
                    <Button
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => void runOpsAction("publish", opsDetail.id)}
                    >
                      Yayınla
                    </Button>
                  )}
                  {actions.includes("unpublish") && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 text-xs"
                      onClick={() => void runOpsAction("unpublish", opsDetail.id)}
                    >
                      Yayından kaldır
                    </Button>
                  )}
                </div>
              ) : null}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Create */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Yeni taslak ürün</DialogTitle>
            <DialogDescription>
              `POST /ops/products/` — ad, kategori_id, ayar_id zorunlu.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={handleCreateSubmit(onCreate)}
            className="flex flex-col gap-3 pt-1"
          >
            <Field label="Ürün adı" error={createErrors.ad?.message}>
              <Input disabled={isCreating} {...registerCreate("ad")} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="kategori_id" error={createErrors.kategori_id?.message}>
                <Input
                  type="number"
                  className="font-mono"
                  disabled={isCreating}
                  {...registerCreate("kategori_id", { valueAsNumber: true })}
                />
              </Field>
              <Field label="ayar_id" error={createErrors.ayar_id?.message}>
                <Input
                  type="number"
                  className="font-mono"
                  disabled={isCreating}
                  {...registerCreate("ayar_id", { valueAsNumber: true })}
                />
              </Field>
            </div>
            <Field label="Açıklama">
              <Input disabled={isCreating} {...registerCreate("aciklama")} />
            </Field>
            <Field label="Fiyat tipi">
              <Input
                disabled={isCreating}
                placeholder="gram"
                {...registerCreate("fiyat_tipi")}
              />
            </Field>
            <Field label="satis_kanali_id (opsiyonel)">
              {channels.length ? (
                <select
                  className="h-9 w-full rounded-[6px] border border-border bg-background px-2 text-xs"
                  disabled={isCreating}
                  {...registerCreate("satis_kanali_id", { valueAsNumber: true })}
                >
                  <option value="">—</option>
                  {channels.map((c) => (
                    <option key={c.id} value={c.id}>
                      #{c.id} {c.ad || ""}
                    </option>
                  ))}
                </select>
              ) : (
                <Input
                  type="number"
                  className="font-mono"
                  disabled={isCreating}
                  {...registerCreate("satis_kanali_id", { valueAsNumber: true })}
                />
              )}
            </Field>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCreateOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isCreating}>
                {isCreating ? "Kaydediliyor…" : "Oluştur"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Variant */}
      <Dialog open={variantOpen} onOpenChange={setVariantOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Varyant ekle</DialogTitle>
            <DialogDescription>
              `POST /ops/products/{"{id}"}/variants/`
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={handleVariantSubmit(onAddVariant)}
            className="flex flex-col gap-3"
          >
            <Field label="Gram">
              <Input
                className="font-mono"
                disabled={isVariantSubmitting}
                {...registerVariant("gram")}
              />
            </Field>
            <Field label="renk_id">
              <Input
                type="number"
                className="font-mono"
                disabled={isVariantSubmitting}
                {...registerVariant("renk_id", { valueAsNumber: true })}
              />
            </Field>
            <Field label="ek_bedel">
              <Input
                className="font-mono"
                disabled={isVariantSubmitting}
                {...registerVariant("ek_bedel")}
              />
            </Field>
            {variantErrors.renk_id ? (
              <span className="text-[11px] text-destructive">
                {variantErrors.renk_id.message}
              </span>
            ) : null}
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setVariantOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isVariantSubmitting}>
                {isVariantSubmitting ? "Ekleniyor…" : "Ekle"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Reject */}
      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Ürünü reddet</DialogTitle>
            <DialogDescription>Red nedeni zorunludur.</DialogDescription>
          </DialogHeader>
          <form
            onSubmit={handleRejectSubmit(onReject)}
            className="flex flex-col gap-3"
          >
            <Field label="Neden" error={rejectErrors.neden?.message}>
              <Input disabled={isRejecting} {...registerReject("neden")} />
            </Field>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setRejectOpen(false)}
              >
                İptal
              </Button>
              <Button
                type="submit"
                size="sm"
                variant="destructive"
                disabled={isRejecting}
              >
                {isRejecting ? "…" : "Reddet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {selectedForCompare.length > 0 && scope === "buyer" && (
        <div className="sticky bottom-4 z-20 flex items-center justify-between rounded-[8px] border border-border bg-card/95 backdrop-blur-sm p-4 shadow-lg">
          <div className="flex items-center gap-2">
            <Scale className="h-4 w-4" />
            <span className="text-xs font-semibold">
              {selectedForCompare.length} ürün seçildi
            </span>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs"
              onClick={() => setSelectedForCompare([])}
            >
              Temizle
            </Button>
            <Button
              size="sm"
              className="h-8 text-xs gap-1.5"
              onClick={() => setCompareModalOpen(true)}
            >
              <Scale className="h-3.5 w-3.5" />
              Karşılaştır
            </Button>
          </div>
        </div>
      )}

      <VariantCompareModal
        open={compareModalOpen}
        onOpenChange={setCompareModalOpen}
        selectedItems={buyerItems.filter((i) =>
          selectedForCompare.includes(i.id)
        )}
        onRemoveItem={(id) =>
          setSelectedForCompare((prev) => prev.filter((i) => i !== id))
        }
        onInspectItem={(id) => void openBuyerDetail(id)}
      />
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
    <div className="rounded-[6px] border border-border px-3 py-2">
      <div className="text-[10px] text-muted-foreground">{label}</div>
      <div className={`text-xs ${mono ? "font-mono" : "font-medium"}`}>{value}</div>
    </div>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label>{label}</Label>
      {children}
      {error ? <span className="text-[11px] text-destructive">{error}</span> : null}
    </div>
  );
}
