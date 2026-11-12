"use client";

import React from "react";
import type { BuyerCatalogItem } from "../types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Eye, X, Scale, Layers, Tag, Gem } from "lucide-react";

interface VariantCompareModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedItems: BuyerCatalogItem[];
  onRemoveItem: (id: number) => void;
  onInspectItem: (id: number) => void;
}

export function VariantCompareModal({
  open,
  onOpenChange,
  selectedItems,
  onRemoveItem,
  onInspectItem,
}: VariantCompareModalProps) {
  if (selectedItems.length === 0) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Scale className="h-5 w-5 text-primary" />
            <DialogTitle>Ürün & Varyant Karşılaştırma</DialogTitle>
          </div>
          <DialogDescription>
            Seçilen platform onaylı ürünlerin teknik özellikleri ve milyem ayar matrisi. (Kör Havuz: Tedarikçi ve maliyet bilgileri gizlidir).
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-2">
          {selectedItems.map((item) => (
            <div
              key={item.id}
              className="flex flex-col justify-between rounded-[8px] border border-border bg-card p-4 space-y-4 relative group"
            >
              {/* Çıkar butonu */}
              <button
                type="button"
                onClick={() => onRemoveItem(item.id)}
                className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors p-1"
                aria-label="Listeden çıkar"
              >
                <X className="h-4 w-4" />
              </button>

              <div className="space-y-3">
                {/* Başlık ve Kod */}
                <div>
                  <Badge variant="outline" className="font-mono text-[10px] mb-1.5">
                    {item.platform_kodu}
                  </Badge>
                  <h3 className="text-sm font-semibold text-foreground line-clamp-2">
                    {item.ad}
                  </h3>
                </div>

                {/* Özellik Listesi */}
                <div className="rounded-[6px] border border-border/60 bg-muted/30 p-3 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-muted-foreground">
                      <Gem className="h-3.5 w-3.5" />
                      <span>Ayar / Milyem</span>
                    </span>
                    <span className="font-mono font-medium text-foreground">
                      {item.ayar ? `${item.ayar} Ayar` : "—"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-muted-foreground">
                      <Layers className="h-3.5 w-3.5" />
                      <span>Kategori</span>
                    </span>
                    <span className="font-medium text-foreground">
                      {item.kategori || "Standart"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-muted-foreground">
                      <Scale className="h-3.5 w-3.5" />
                      <span>Varyant Sayısı</span>
                    </span>
                    <span className="font-mono tabular-nums font-semibold text-foreground">
                      {item.varyant_count} Seçenek
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-muted-foreground">
                      <Tag className="h-3.5 w-3.5" />
                      <span>Fiyat Modeli</span>
                    </span>
                    <Badge variant="secondary" className="font-mono text-[10px]">
                      {item.fiyat_tipi || "ONS_BAZLI"}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Alt Aksiyon */}
              <div className="pt-2 border-t border-border/60">
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => {
                    onOpenChange(false);
                    onInspectItem(item.id);
                  }}
                  className="w-full text-xs gap-1.5"
                >
                  <Eye className="h-3.5 w-3.5" />
                  <span>Varyantları Gör & Quote İste</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
