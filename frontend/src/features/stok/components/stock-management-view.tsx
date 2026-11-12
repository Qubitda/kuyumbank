"use client";

import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { stokService } from "../services";
import { stockAdjustmentSchema, type StockAdjustmentInput } from "../schemas";
import type { StockBalance } from "../types";
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
      warehouse_id: undefined,
      teklif_id: undefined,
      miktar: "",
      neden: "",
    },
  });

  const fetchStock = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await stokService.listSupplierStock();
      setBalances(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stok verisi alınamadı.");
      setBalances([]);
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
        warehouse_id: Number(data.warehouse_id),
        teklif_id: Number(data.teklif_id),
        miktar: data.miktar,
        neden: data.neden,
      });
      setAdjustSuccess("Stok düzeltmesi kaydedildi.");
      reset();
      setAdjustOpen(false);
      await fetchStock();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stok hareketi işlenemedi.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Stok & Depo Dengesi
          </h1>
          <p className="text-xs text-muted-foreground">
            `GET /supplier/stock/` — available / reserved / on_hand.
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
          <span>Stok Düzeltmesi</span>
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

      <div className="rounded-[8px] border border-border bg-card overflow-hidden">
        {loading ? (
          <div className="flex h-48 w-full items-center justify-center">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Stok dengesi yükleniyor…</span>
            </div>
          </div>
        ) : balances.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center gap-2 text-center p-6 text-xs text-muted-foreground">
            <Boxes className="h-8 w-8 opacity-40 mb-1" />
            <span className="text-sm font-medium text-foreground">Veri bulunamadı</span>
            <span className="max-w-sm">Tedarikçi stok bakiyesi dönmedi.</span>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Depo</TableHead>
                <TableHead>Teklif</TableHead>
                <TableHead>Varyant</TableHead>
                <TableHead>Birim</TableHead>
                <TableHead className="text-right">On Hand</TableHead>
                <TableHead className="text-right">Reserved</TableHead>
                <TableHead className="text-right">Available</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {balances.map((b) => (
                <TableRow
                  key={`${b.warehouse_id ?? "w"}-${b.teklif_id ?? "t"}-${b.varyant_id}`}
                >
                  <TableCell className="font-mono text-xs">
                    {b.warehouse_id != null ? `#${b.warehouse_id}` : "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {b.teklif_id != null ? `#${b.teklif_id}` : "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs font-medium">
                    #{b.varyant_id}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{b.birim}</TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {b.on_hand ?? "—"}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums text-muted-foreground">
                    {b.reserved ?? "—"}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums font-semibold">
                    {b.available}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <Dialog open={adjustOpen} onOpenChange={setAdjustOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Stok Düzeltmesi</DialogTitle>
            <DialogDescription>
              `POST /supplier/stock/adjustments/` — warehouse_id, teklif_id, miktar.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit(onAdjustSubmit)} className="flex flex-col gap-4 pt-2">
            <div className="space-y-1.5">
              <Label htmlFor="warehouse_id">Warehouse ID</Label>
              <Input
                id="warehouse_id"
                type="number"
                className="font-mono"
                {...register("warehouse_id", { valueAsNumber: true })}
              />
              {errors.warehouse_id && (
                <p className="text-xs text-destructive">{errors.warehouse_id.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="teklif_id">Teklif ID</Label>
              <Input
                id="teklif_id"
                type="number"
                className="font-mono"
                {...register("teklif_id", { valueAsNumber: true })}
              />
              {errors.teklif_id && (
                <p className="text-xs text-destructive">{errors.teklif_id.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="miktar">Miktar</Label>
              <Input id="miktar" className="font-mono" {...register("miktar")} />
              {errors.miktar && (
                <p className="text-xs text-destructive">{errors.miktar.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="neden">Neden</Label>
              <Input id="neden" {...register("neden")} />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setAdjustOpen(false)}>
                İptal
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                Kaydet
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
