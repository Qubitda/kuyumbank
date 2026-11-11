"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { stokService } from "../services";
import { stockAdjustmentSchema, type StockAdjustmentInput } from "../schemas";
import type { StockBalance } from "../types";
import { formatGram } from "@/lib/format";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Boxes, RefreshCw, AlertCircle, Plus } from "lucide-react";

export function StockManagementView() {
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [adjustOpen, setAdjustOpen] = useState(false);
  const [adjustSuccess, setAdjustSuccess] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<StockAdjustmentInput>({
    resolver: zodResolver(stockAdjustmentSchema),
    defaultValues: {
      varyant_id: undefined,
      miktar: "",
      aciklama: "",
    },
  });

  const fetchStock = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await stokService.getSupplierStock();
      setBalances(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stok verisi alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStock();
  }, []);

  const onAdjustSubmit = async (data: StockAdjustmentInput) => {
    setError(null);
    setAdjustSuccess(null);
    try {
      await stokService.adjustStock({
        varyant_id: Number(data.varyant_id),
        miktar: data.miktar,
        aciklama: data.aciklama,
      });
      setAdjustSuccess("Stok hareketi ledger defterine başarıyla işlendi.");
      reset();
      setAdjustOpen(false);
      await fetchStock();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stok hareketi işlenemedi.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık ve Düzeltme Butonu */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Stok & Depo Dengesi
          </h1>
          <p className="text-xs text-muted-foreground">
            StockMovement defter projeksiyonu, rezerve TTL miktarları ve ATP takibi.
          </p>
        </div>

        <Button
          onClick={() => {
            setAdjustSuccess(null);
            setAdjustOpen(true);
          }}
          className="gap-2"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          <span>Stok Hareketi Ekle</span>
        </Button>
      </div>

      {adjustSuccess && (
        <div className="rounded-[6px] border border-border bg-muted/60 p-3 text-xs text-foreground font-medium">
          {adjustSuccess}
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
            onClick={fetchStock}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      {/* Stok Dengesi Tablosu */}
      <div className="rounded-[8px] border border-border bg-card overflow-hidden">
        {loading ? (
          <div className="flex h-48 w-full items-center justify-center">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Stok dengesi hesaplanıyor…</span>
            </div>
          </div>
        ) : balances.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center gap-2 text-center p-6 text-xs text-muted-foreground">
            <Boxes className="h-8 w-8 opacity-40 mb-1" />
            <span className="text-sm font-medium text-foreground">Stok hareketi bulunamadı</span>
            <span className="max-w-sm">
              Tedarikçi stoğu için tanımlı depo bakiyesi bulunmamaktadır.
            </span>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Depo ID</TableHead>
                <TableHead>Varyant ID</TableHead>
                <TableHead className="text-right">Fiziksel Mevcut</TableHead>
                <TableHead className="text-right">Rezerve (Hold)</TableHead>
                <TableHead className="text-right">Kullanılabilir (ATP)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {balances.map((b) => (
                <TableRow key={b.id || `${b.depo_id}-${b.varyant_id}`}>
                  <TableCell className="font-mono text-xs">
                    Depo #{b.depo_id}
                  </TableCell>
                  <TableCell className="font-mono text-xs font-medium">
                    #{b.varyant_id}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums text-foreground">
                    {formatGram(b.mevcut_miktar)}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums text-muted-foreground">
                    {formatGram(b.rezerve_miktar)}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums font-semibold text-foreground">
                    {formatGram(b.kullanilabilir_miktar)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Stok Düzeltme Dialog */}
      <Dialog open={adjustOpen} onOpenChange={setAdjustOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Stok Hareketi Girişi</DialogTitle>
            <DialogDescription>
              StockMovement defterine immutable yeni hareket kaydı ekler.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onAdjustSubmit)} className="flex flex-col gap-4 pt-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="stock-variant-id">Varyant ID</Label>
              <Input
                id="stock-variant-id"
                type="number"
                placeholder="Örn: 101"
                disabled={isSubmitting}
                {...register("varyant_id", { valueAsNumber: true })}
              />
              {errors.varyant_id && (
                <span className="text-[11px] text-destructive">
                  {errors.varyant_id.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="stock-amount">Miktar (Gram / Adet)</Label>
              <Input
                id="stock-amount"
                type="text"
                placeholder="Örn: 50.00 veya -10.00"
                disabled={isSubmitting}
                {...register("miktar")}
              />
              {errors.miktar && (
                <span className="text-[11px] text-destructive">
                  {errors.miktar.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="stock-desc">Açıklama / Referans</Label>
              <Input
                id="stock-desc"
                type="text"
                placeholder="Depo sayım düzeltmesi"
                disabled={isSubmitting}
                {...register("aciklama")}
              />
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setAdjustOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? "Kaydediliyor…" : "Deftere Yaz"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
