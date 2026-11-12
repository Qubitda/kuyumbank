"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  useAddMeasurementMutation,
  useCancelInspectionMutation,
  useFailInspectionMutation,
  useInspectionsQuery,
  usePassInspectionMutation,
  useStartInspectionMutation,
} from "../hooks";
import {
  measurementSchema,
  toOpsMeasurementBody,
  type MeasurementInput,
} from "../schemas";
import type { OpsInspection } from "../types";
import { useActionToast } from "@/hooks/use-action-toast";
import { mapCommerceError } from "@/lib/api/commerce-errors";
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
  CheckCircle2,
  XCircle,
  Play,
  Scale,
  RefreshCw,
  AlertCircle,
  Ban,
} from "lucide-react";

export function QualityInspectionsView() {
  const actionToast = useActionToast();
  const listQ = useInspectionsQuery();
  const startMut = useStartInspectionMutation();
  const passMut = usePassInspectionMutation();
  const failMut = useFailInspectionMutation();
  const cancelMut = useCancelInspectionMutation();
  const measureMut = useAddMeasurementMutation();

  const [measureModalOpen, setMeasureModalOpen] = useState(false);
  const [selectedInspection, setSelectedInspection] =
    useState<OpsInspection | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<MeasurementInput>({
    resolver: zodResolver(measurementSchema),
    defaultValues: {
      order_line_id: undefined,
      olculen_ayar: "",
      olculen_gram: "",
      override_gerekce: "",
    },
  });

  const inspections = listQ.data ?? [];
  const loading = listQ.isLoading;
  const error = listQ.isError
    ? mapCommerceError(listQ.error, "Kalite kontrol listesi alınamadı.")
    : null;

  const runAction = async (
    label: string,
    fn: () => Promise<unknown>
  ) => {
    try {
      await fn();
      actionToast.success(label);
    } catch (err) {
      actionToast.error(label, err);
    }
  };

  const onMeasurementSubmit = async (formData: MeasurementInput) => {
    if (!selectedInspection) return;
    try {
      const body = toOpsMeasurementBody(formData);
      await measureMut.mutateAsync({ id: selectedInspection.id, data: body });
      actionToast.success("Ölçüm kaydedildi");
      setMeasureModalOpen(false);
      reset();
    } catch (err) {
      actionToast.error("Ölçüm kaydedilemedi", err);
    }
  };

  const renderDurumBadge = (durum: string) => {
    switch (durum) {
      case "GECTI":
        return <Badge variant="success">GEÇTİ</Badge>;
      case "KALDI":
        return <Badge variant="destructive">KALDI</Badge>;
      case "IPTAL":
        return <Badge variant="destructive">İPTAL</Badge>;
      case "INCELEMEDE":
        return <Badge variant="secondary">İNCELEMEDE</Badge>;
      case "BEKLEMEDE":
      default:
        return <Badge variant="outline">{durum || "BEKLEMEDE"}</Badge>;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 border-b border-border pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Kalite Kontrol (QC)
          </h1>
          <p className="text-xs text-muted-foreground">
            OpenAPI ölçüm: `order_line_id` + `olculen` (ayar/gram ayrı alan
            GAP-F4-02 — UI birleştirir).
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void listQ.refetch()}
          className="gap-1.5"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Yenile
        </Button>
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
            onClick={() => void listQ.refetch()}
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
              <span>İnceleme listesi alınıyor…</span>
            </div>
          </div>
        ) : inspections.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            Şu an bekleyen veya aktif kalite kontrol incelemesi bulunmamaktadır.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">İnceleme ID</TableHead>
                <TableHead>Sipariş Ref</TableHead>
                <TableHead>Durum</TableHead>
                <TableHead className="text-right">İşlemler</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {inspections.map((item) => {
                const actions = item.allowed_actions || [];
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono text-xs font-semibold tabular-nums">
                      QC-#{item.id}
                    </TableCell>
                    <TableCell className="font-mono text-xs tabular-nums">
                      {item.order_id != null ? `Sipariş #${item.order_id}` : "—"}
                    </TableCell>
                    <TableCell>{renderDurumBadge(item.durum)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5 flex-wrap">
                        {actions.includes("start") && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              void runAction("İnceleme başlatıldı", () =>
                                startMut.mutateAsync(item.id)
                              )
                            }
                            className="h-8 text-xs gap-1"
                          >
                            <Play className="h-3.5 w-3.5" />
                            Başlat
                          </Button>
                        )}
                        {actions.includes("measure") && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setSelectedInspection(item);
                              setMeasureModalOpen(true);
                            }}
                            className="h-8 text-xs gap-1"
                          >
                            <Scale className="h-3.5 w-3.5" />
                            Ölçüm Gir
                          </Button>
                        )}
                        {actions.includes("pass") && (
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() =>
                              void runAction("Geçti olarak işaretlendi", () =>
                                passMut.mutateAsync(item.id)
                              )
                            }
                            className="h-8 text-xs gap-1"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Onayla
                          </Button>
                        )}
                        {actions.includes("fail") && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() =>
                              void runAction("Kaldı olarak işaretlendi", () =>
                                failMut.mutateAsync(item.id)
                              )
                            }
                            className="h-8 text-xs gap-1"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            Reddet
                          </Button>
                        )}
                        {actions.includes("cancel") && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              void runAction("İnceleme iptal edildi", () =>
                                cancelMut.mutateAsync(item.id)
                              )
                            }
                            className="h-8 text-xs gap-1"
                          >
                            <Ban className="h-3.5 w-3.5" />
                            İptal
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

      <Dialog open={measureModalOpen} onOpenChange={setMeasureModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Ölçüm Kaydı (QC-#{selectedInspection?.id})</DialogTitle>
            <DialogDescription>
              API `olculen` string bekler; ayar/gram burada birleştirilir
              (GAP-F4-02).
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={handleSubmit(onMeasurementSubmit)}
            className="flex flex-col gap-4 pt-2"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="qc-line">Sipariş satırı (order_line_id)</Label>
              <Input
                id="qc-line"
                type="number"
                className="font-mono tabular-nums"
                disabled={isSubmitting}
                {...register("order_line_id", { valueAsNumber: true })}
              />
              {errors.order_line_id && (
                <span className="text-[11px] text-destructive">
                  {errors.order_line_id.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="qc-ayar">Ölçülen Ayar</Label>
              <Input
                id="qc-ayar"
                placeholder="Örn: 14"
                className="font-mono tabular-nums"
                disabled={isSubmitting}
                {...register("olculen_ayar")}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="qc-gram">Ölçülen Gram</Label>
              <Input
                id="qc-gram"
                placeholder="Örn: 12.450"
                className="font-mono tabular-nums"
                disabled={isSubmitting}
                {...register("olculen_gram")}
              />
              {errors.olculen && (
                <span className="text-[11px] text-destructive">
                  {errors.olculen.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="qc-override">Override gerekçe</Label>
              <Input
                id="qc-override"
                disabled={isSubmitting}
                {...register("override_gerekce")}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setMeasureModalOpen(false)}
              >
                İptal
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={isSubmitting || measureMut.isPending}
              >
                {isSubmitting || measureMut.isPending
                  ? "Kaydediliyor…"
                  : "Ölçümü Kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
