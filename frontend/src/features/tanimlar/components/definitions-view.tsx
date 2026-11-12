"use client";

import React, { useMemo, useState } from "react";
import { useSalesChannels } from "../hooks";
import type {
  DefinitionCategoryId,
  DefinitionCategoryMeta,
  SalesChannel,
} from "../types";
import { formatDateTime } from "@/lib/format";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Sliders,
  RefreshCw,
  AlertCircle,
  Search,
  Eye,
  Lock,
  Layers,
} from "lucide-react";

const PAGE_SIZE = 10;

const CATEGORIES: DefinitionCategoryMeta[] = [
  {
    id: "sales-channels",
    label: "Satış Kanalları",
    description: "Quote TTL ve satış kanalı keşfi (GET /sales-channels/).",
    backendModel: "tanimlar.SatisKanali",
    apiAvailable: true,
    endpoint: "/api/v1/sales-channels/",
  },
  {
    id: "fiyat-gruplari",
    label: "Fiyat Grupları",
    description: "Alıcı fiyat grubu tanımları.",
    backendModel: "tanimlar.FiyatGrubu",
    apiAvailable: false,
  },
  {
    id: "ayar-milyem",
    label: "Ayar / Milyem",
    description: "Metal ayar ve milyem katsayıları.",
    backendModel: "tanimlar.AyarMilyem",
    apiAvailable: false,
  },
  {
    id: "kur-metal",
    label: "Metal Kurları",
    description: "XAU ve değerli metal kur kayıtları.",
    backendModel: "tanimlar.MetalKuru",
    apiAvailable: false,
  },
  {
    id: "kur-doviz",
    label: "Döviz Kurları",
    description: "TRY çapraz döviz kurları.",
    backendModel: "tanimlar.DovizKuru",
    apiAvailable: false,
  },
];

type SortKey = "kod_asc" | "kod_desc" | "ad_asc" | "ad_desc" | "ttl_asc" | "ttl_desc";

function matchesQuery(row: SalesChannel, q: string): boolean {
  if (!q) return true;
  const hay = `${row.kod} ${row.ad} ${row.id}`.toLowerCase();
  return hay.includes(q.toLowerCase());
}

function sortChannels(rows: SalesChannel[], sort: SortKey): SalesChannel[] {
  const copy = [...rows];
  copy.sort((a, b) => {
    switch (sort) {
      case "kod_desc":
        return b.kod.localeCompare(a.kod, "tr");
      case "ad_asc":
        return a.ad.localeCompare(b.ad, "tr");
      case "ad_desc":
        return b.ad.localeCompare(a.ad, "tr");
      case "ttl_asc":
        return (a.quote_ttl_saniye ?? -1) - (b.quote_ttl_saniye ?? -1);
      case "ttl_desc":
        return (b.quote_ttl_saniye ?? -1) - (a.quote_ttl_saniye ?? -1);
      case "kod_asc":
      default:
        return a.kod.localeCompare(b.kod, "tr");
    }
  });
  return copy;
}

export function DefinitionsView() {
  const { page, channels, loading, error, refresh } = useSalesChannels();
  const [categoryId, setCategoryId] = useState<DefinitionCategoryId>("sales-channels");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("kod_asc");
  const [pageIndex, setPageIndex] = useState(0);
  const [selected, setSelected] = useState<SalesChannel | null>(null);

  const activeCategory = CATEGORIES.find((c) => c.id === categoryId) || CATEGORIES[0];

  const filtered = useMemo(() => {
    const matched = channels.filter((c) => matchesQuery(c, query.trim()));
    return sortChannels(matched, sort);
  }, [channels, query, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(pageIndex, totalPages - 1);
  const paged = filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);

  const totalCount = page?.count ?? channels.length;
  const activeCount = channels.length;
  const passiveCount = 0;
  const categoryCount = CATEGORIES.filter((c) => c.apiAvailable).length;

  const onSelectCategory = (id: DefinitionCategoryId) => {
    setCategoryId(id);
    setQuery("");
    setPageIndex(0);
    setSelected(null);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 border-b border-border pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Tanımlar
          </h1>
          <p className="text-xs text-muted-foreground max-w-[52ch] leading-relaxed">
            Platform parametreleri. Yazma uçları yalnızca OpenAPI’de varsa aktiftir;
            şu an HTTP yüzeyi: satış kanalları listesi.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5 self-start"
          onClick={() => void refresh()}
          disabled={loading}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Yenile
        </Button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Toplam kayıt" value={String(totalCount)} />
        <StatCard label="Aktif (API)" value={String(activeCount)} />
        <StatCard label="Pasif (API)" value={String(passiveCount)} hint="Liste yalnız aktif döner" />
        <StatCard label="HTTP kategorisi" value={String(categoryCount)} />
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
            onClick={() => void refresh()}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[240px_minmax(0,1fr)] gap-4">
        <nav
          className="rounded-[8px] border border-border bg-card p-2 h-fit"
          aria-label="Tanım kategorileri"
        >
          <div className="px-2 py-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Kategoriler
          </div>
          <ul className="flex flex-col gap-0.5">
            {CATEGORIES.map((cat) => {
              const selectedCat = cat.id === categoryId;
              const count =
                cat.id === "sales-channels" && cat.apiAvailable ? channels.length : null;
              return (
                <li key={cat.id}>
                  <button
                    type="button"
                    onClick={() => onSelectCategory(cat.id)}
                    className={`w-full rounded-[6px] px-2.5 py-2 text-left transition-colors ${
                      selectedCat
                        ? "bg-muted text-foreground"
                        : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium">{cat.label}</span>
                      {cat.apiAvailable ? (
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {count ?? "—"}
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="font-mono text-[10px]">
                          HTTP yok
                        </Badge>
                      )}
                    </div>
                    <p className="mt-0.5 text-[11px] text-muted-foreground line-clamp-2">
                      {cat.description}
                    </p>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <section className="rounded-[8px] border border-border bg-card overflow-hidden min-w-0">
          <div className="border-b border-border px-4 py-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-2 min-w-0">
              <Sliders className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
              <div className="min-w-0">
                <h2 className="text-sm font-semibold text-foreground">
                  {activeCategory.label}
                </h2>
                <p className="text-[11px] text-muted-foreground font-mono truncate">
                  {activeCategory.backendModel}
                  {activeCategory.endpoint ? ` · ${activeCategory.endpoint}` : ""}
                </p>
              </div>
            </div>
          </div>

          {!activeCategory.apiAvailable ? (
            <div className="flex h-56 flex-col items-center justify-center gap-2 p-6 text-center text-xs text-muted-foreground">
              <Lock className="h-7 w-7 opacity-40" />
              <span className="text-sm font-medium text-foreground">
                HTTP API yüzeyi yok
              </span>
              <span className="max-w-md leading-relaxed">
                Bu tanım Django modelinde mevcut ancak OpenAPI sözleşmesinde list/create/update
                ucu bulunmuyor. Sahte CRUD oluşturulmadı; yönetim admin veya sonraki API
                diliminde yapılabilir.
              </span>
            </div>
          ) : loading ? (
            <div className="flex h-56 items-center justify-center gap-2 text-xs text-muted-foreground">
              <RefreshCw className="h-4 w-4 animate-spin" />
              Tanımlar yükleniyor…
            </div>
          ) : (
            <>
              <div className="border-b border-border px-4 py-3 flex flex-col gap-2 sm:flex-row sm:items-center">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setPageIndex(0);
                    }}
                    placeholder="Kod veya ad ara…"
                    className="pl-8 h-9"
                    aria-label="Tanım ara"
                  />
                </div>
                <select
                  value={sort}
                  onChange={(e) => {
                    setSort(e.target.value as SortKey);
                    setPageIndex(0);
                  }}
                  className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs text-foreground"
                  aria-label="Sıralama"
                >
                  <option value="kod_asc">Kod (A→Z)</option>
                  <option value="kod_desc">Kod (Z→A)</option>
                  <option value="ad_asc">Ad (A→Z)</option>
                  <option value="ad_desc">Ad (Z→A)</option>
                  <option value="ttl_asc">Quote TTL ↑</option>
                  <option value="ttl_desc">Quote TTL ↓</option>
                </select>
              </div>

              {filtered.length === 0 ? (
                <div className="flex h-48 flex-col items-center justify-center gap-2 p-6 text-center text-xs text-muted-foreground">
                  <Layers className="h-7 w-7 opacity-40" />
                  <span className="text-sm font-medium text-foreground">
                    Veri bulunamadı
                  </span>
                  <span>
                    {channels.length === 0
                      ? "Aktif satış kanalı dönmedi."
                      : "Arama ölçütlerine uygun kayıt yok."}
                  </span>
                </div>
              ) : (
                <>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[100px]">Kod</TableHead>
                        <TableHead>Ad</TableHead>
                        <TableHead className="text-right">Quote TTL (sn)</TableHead>
                        <TableHead>Durum</TableHead>
                        <TableHead className="text-right">İşlem</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paged.map((row) => (
                        <TableRow key={row.id}>
                          <TableCell className="font-mono text-xs font-semibold">
                            {row.kod}
                          </TableCell>
                          <TableCell className="font-medium text-foreground">
                            {row.ad}
                          </TableCell>
                          <TableCell className="text-right font-mono tabular-nums text-xs">
                            {row.quote_ttl_saniye != null ? row.quote_ttl_saniye : "—"}
                          </TableCell>
                          <TableCell>
                            <Badge variant="success" className="font-mono text-[10px]">
                              AKTİF
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 gap-1.5 text-xs"
                              onClick={() => setSelected(row)}
                            >
                              <Eye className="h-3.5 w-3.5" />
                              Detay
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>

                  <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-3 text-xs text-muted-foreground">
                    <span>
                      {filtered.length} kayıt · sayfa {safePage + 1}/{totalPages}
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8"
                        disabled={safePage <= 0}
                        onClick={() => setPageIndex((p) => Math.max(0, p - 1))}
                      >
                        Önceki
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8"
                        disabled={safePage >= totalPages - 1}
                        onClick={() =>
                          setPageIndex((p) => Math.min(totalPages - 1, p + 1))
                        }
                      >
                        Sonraki
                      </Button>
                    </div>
                  </div>
                </>
              )}

              <div className="border-t border-border px-4 py-3 text-[11px] text-muted-foreground leading-relaxed">
                Yazma (POST/PATCH/DELETE) ve pasif listeleme uçları sözleşmede yok.
                Yeni kayıt / düzenleme / silme butonları bilerek eklenmedi.
                {page?.server_now
                  ? ` · Sunucu: ${formatDateTime(page.server_now)}`
                  : null}
              </div>
            </>
          )}
        </section>
      </div>

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Satış kanalı detayı</DialogTitle>
            <DialogDescription>
              Salt okunur — `GET /sales-channels/` alanları.
            </DialogDescription>
          </DialogHeader>
          {selected && (
            <div className="flex flex-col gap-3 pt-1 text-sm">
              <DetailRow label="ID" value={`#${selected.id}`} mono />
              <DetailRow label="Kod" value={selected.kod} mono />
              <DetailRow label="Ad" value={selected.ad} />
              <DetailRow
                label="Quote TTL"
                value={
                  selected.quote_ttl_saniye != null
                    ? `${selected.quote_ttl_saniye} sn`
                    : "Tanımsız (quote üretilmez)"
                }
                mono
              />
              <DetailRow label="Durum" value="AKTİF (API filtresi)" />
              <DetailRow label="Model" value="tanimlar.SatisKanali" mono />
              <div className="pt-2 flex justify-end">
                <Button variant="outline" size="sm" onClick={() => setSelected(null)}>
                  Kapat
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-[8px] border border-border bg-card p-4 space-y-1">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="text-xl font-semibold font-mono tabular-nums text-foreground">
        {value}
      </div>
      {hint ? <div className="text-[10px] text-muted-foreground">{hint}</div> : null}
    </div>
  );
}

function DetailRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-2">
      <span className="text-xs text-muted-foreground shrink-0">{label}</span>
      <span
        className={`text-xs text-foreground text-right ${mono ? "font-mono" : "font-medium"}`}
      >
        {value}
      </span>
    </div>
  );
}
