"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { kaliteService } from "../services";
import { measurementSchema, type MeasurementInput } from "../schemas";
import type { OpsInspection } from "../types";
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
import { CheckCircle2, XCircle, Play, Scale, RefreshCw, AlertCircle } from "lucide-react";

export function QualityInspectionsView() {
  const [inspections, setInspections] = useState<OpsInspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [measureModalOpen, setMeasureModalOpen] = useState(false);
  const [selectedInspection, setSelectedInspection] = useState<OpsInspection | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<MeasurementInput>({
    resolver: zodResolver(measurementSchema),
    defaultValues: {
      olculen_ayar: "",
      olculen_gram: "",
      notlar: "",
    },
  });

  const fetchInspections = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await kaliteService.getInspections();
      setInspections(data?.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kalite kontrol listesi alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInspections();
  }, []);

  const handleStart = async (id: number) => {
    try {
      await kaliteService.startInspection(id);
      await fetchInspections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "İnceleme başlatılamadı.");
    }
  };

  const handlePass = async (id: number) => {
    try {
      await kaliteService.passInspection(id);
      await fetchInspections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Onaylama başarısız.");
    }
  };

  const handleFail = async (id: number) => {
    try {
      await kaliteService.failInspection(id);
      await fetchInspections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ret işlemi başarısız.");
    }
  };

  const onMeasurementSubmit = async (formData: MeasurementInput) => {
    if (!selectedInspection) return;
    try {
      await kaliteService.addMeasurement(selectedInspection.id, formData);
      setMeasureModalOpen(false);
      reset();
      await fetchInspections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ölçüm kaydedilemedi.");
    }
  };

  const renderDurumBadge = (durum: string) => {
    switch (durum) {
      case "GECTI":
        return <Badge variant="success">GEÇTİ</Badge>;
      case "KALDI":
      case "IPTAL":
        return <Badge variant="destructive">KALDI</Badge>;
      case "INCELEMEDE":
        return <Badge variant="secondary">İNCELEMEDE</Badge>;
      case "BEKLEMEDE":
      default:
        return <Badge variant="outline">BEKLEMEDE</Badge>;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık */}
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Kalite Kontrol (QC Inspection SM)
        </h1>
        <p className="text-xs text-muted-foreground">
          Sipariş bazlı ayar, gram ve tolerans kontrolleri. Durum makinesi platform denetimindedir.
        </p>
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
            onClick={fetchInspections}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      {/* Tablo */}
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
                <TableHead className="text-right">İşlemler (Durum Makinesi)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {inspections.map((item) => {
                const actions = item.allowed_actions || [];
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono text-xs font-semibold">
                      QC-#{item.id}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      Sipariş #{item.order_id}
                    </TableCell>
                    <TableCell>{renderDurumBadge(item.durum)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {actions.includes("start") && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleStart(item.id)}
                            className="h-8 text-xs gap-1"
                          >
                            <Play className="h-3.5 w-3.5" />
                            <span>Başlat</span>
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
                            <span>Ölçüm Gir</span>
                          </Button>
                        )}
                        {actions.includes("pass") && (
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => handlePass(item.id)}
                            className="h-8 text-xs gap-1"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            <span>Onayla (Geçti)</span>
                          </Button>
                        )}
                        {actions.includes("fail") && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleFail(item.id)}
                            className="h-8 text-xs gap-1"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            <span>Reddet (Kaldı)</span>
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

      {/* Ölçüm Giriş Dialog */}
      <Dialog open={measureModalOpen} onOpenChange={setMeasureModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Ölçüm Kaydı (QC-#{selectedInspection?.id})</DialogTitle>
            <DialogDescription>
              Fiziksel ayar ve hassas terazi tartım değerlerini girin.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onMeasurementSubmit)} className="flex flex-col gap-4 pt-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="qc-ayar">Ölçülen Ayar</Label>
              <Input
                id="qc-ayar"
                placeholder="Örn: 14 veya 585 milyem"
                disabled={isSubmitting}
                {...register("olculen_ayar")}
              />
              {errors.olculen_ayar && (
                <span className="text-[11px] text-destructive">
                  {errors.olculen_ayar.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="qc-gram">Ölçülen Gram</Label>
              <Input
                id="qc-gram"
                placeholder="Örn: 12.450"
                disabled={isSubmitting}
                {...register("olculen_gram")}
              />
              {errors.olculen_gram && (
                <span className="text-[11px] text-destructive">
                  {errors.olculen_gram.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="qc-notes">Kontrol Notları</Label>
              <Input
                id="qc-notes"
                placeholder="Görsel kusur yok, damga kontrolü tamam"
                disabled={isSubmitting}
                {...register("notlar")}
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
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? "Kaydediliyor…" : "Ölçümü Kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
