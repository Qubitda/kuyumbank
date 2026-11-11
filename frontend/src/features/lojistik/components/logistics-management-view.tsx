"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { lojistikService } from "../services";
import { shipmentDispatchSchema, type ShipmentDispatchInput } from "../schemas";
import type { OpsShipment, BuyerReturn } from "../types";
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
  Truck,
  RotateCcw,
  RefreshCw,
  AlertCircle,
  PackageCheck,
  Send,
  CheckCircle2,
} from "lucide-react";

export function LogisticsManagementView() {
  const [activeTab, setActiveTab] = useState<"shipments" | "returns">("shipments");

  const [shipments, setShipments] = useState<OpsShipment[]>([]);
  const [returns, setReturns] = useState<BuyerReturn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [dispatchModalOpen, setDispatchModalOpen] = useState(false);
  const [selectedShipment, setSelectedShipment] = useState<OpsShipment | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ShipmentDispatchInput>({
    resolver: zodResolver(shipmentDispatchSchema),
    defaultValues: {
      tasiyici: "Loomis / Brinks Sigortalı Değerli Kargo",
      takip_no: "",
    },
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [shipmentRes, returnRes] = await Promise.allSettled([
        lojistikService.getShipments(),
        lojistikService.getReturns(),
      ]);

      if (shipmentRes.status === "fulfilled") {
        setShipments(shipmentRes.value?.results || []);
      }
      if (returnRes.status === "fulfilled") {
        setReturns(returnRes.value?.results || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lojistik verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handlePrepare = async (id: number) => {
    try {
      await lojistikService.prepareShipment(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hazırlık başlatılamadı.");
    }
  };

  const handleDeliver = async (id: number) => {
    try {
      await lojistikService.deliverShipment(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Teslimat onaylanamadı.");
    }
  };

  const onDispatchSubmit = async (formData: ShipmentDispatchInput) => {
    if (!selectedShipment) return;
    try {
      await lojistikService.dispatchShipment(selectedShipment.id, formData);
      setDispatchModalOpen(false);
      reset();
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sevk işlemi kaydedilemedi.");
    }
  };

  const handleApproveReturn = async (id: number) => {
    try {
      await lojistikService.approveReturn(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "İade onaylanamadı.");
    }
  };

  const handleMahsupReturn = async (id: number) => {
    try {
      await lojistikService.mahsupReturn(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "İade mahsup edilemedi.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık ve Sekmeler */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Lojistik & Sevkiyat Operasyonları
          </h1>
          <p className="text-xs text-muted-foreground">
            Sigortalı kargo takip, teslimat kanıtı (POD) ve iade durum makinesi yönetimi.
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-[6px] border border-border bg-muted/40 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("shipments")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "shipments"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Truck className="h-3.5 w-3.5" />
            <span>Sevkiyatlar ({shipments.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("returns")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "returns"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>İade Talepleri ({returns.length})</span>
          </button>
        </div>
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
            <span>Sevkiyat verileri alınıyor…</span>
          </div>
        </div>
      ) : activeTab === "shipments" ? (
        /* Sevkiyatlar Tablosu */
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          {shipments.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Kayıtlı sevkiyat bulunmamaktadır.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Sevkiyat ID</TableHead>
                  <TableHead>Sipariş Ref</TableHead>
                  <TableHead>Taşıyıcı / Takip No</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">Durum Makinesi İşlemleri</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shipments.map((s) => {
                  const actions = s.allowed_actions || [];
                  return (
                    <TableRow key={s.id}>
                      <TableCell className="font-mono text-xs font-semibold">
                        SHP-#{s.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        Sipariş #{s.order_id}
                      </TableCell>
                      <TableCell className="text-xs">
                        {s.tasiyici ? (
                          <div className="flex flex-col">
                            <span className="font-medium text-foreground">{s.tasiyici}</span>
                            <span className="font-mono text-[11px] text-muted-foreground">{s.takip_no || "—"}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">Henüz atanmadı</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            s.durum === "TESLIM_EDILDI"
                              ? "success"
                              : s.durum === "SEVK_EDILDI"
                              ? "warning"
                              : "outline"
                          }
                          className="font-mono text-[10px]"
                        >
                          {s.durum}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {actions.includes("prepare") && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handlePrepare(s.id)}
                              className="h-8 text-xs gap-1"
                            >
                              <PackageCheck className="h-3.5 w-3.5" />
                              <span>Hazırla</span>
                            </Button>
                          )}
                          {actions.includes("dispatch") && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => {
                                setSelectedShipment(s);
                                setDispatchModalOpen(true);
                              }}
                              className="h-8 text-xs gap-1"
                            >
                              <Send className="h-3.5 w-3.5" />
                              <span>Sevk Et</span>
                            </Button>
                          )}
                          {actions.includes("deliver") && (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => handleDeliver(s.id)}
                              className="h-8 text-xs gap-1"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span>Teslim Alındı (POD)</span>
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
        /* İade Talepleri Tablosu */
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          {returns.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Aktif iade talebi bulunmamaktadır.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">İade ID</TableHead>
                  <TableHead>Sipariş Ref</TableHead>
                  <TableHead>İade Nedeni</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlem</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {returns.map((r) => {
                  const actions = r.allowed_actions || [];
                  return (
                    <TableRow key={r.id}>
                      <TableCell className="font-mono text-xs font-semibold">
                        RET-#{r.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        Sipariş #{r.order_id}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {r.sebep || "Standart İade"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={r.durum === "MAHSUP_EDILDI" ? "success" : "outline"}
                          className="font-mono text-[10px]"
                        >
                          {r.durum}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {actions.includes("approve") && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleApproveReturn(r.id)}
                              className="h-8 text-xs"
                            >
                              Onayla
                            </Button>
                          )}
                          {actions.includes("mahsup") && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => handleMahsupReturn(r.id)}
                              className="h-8 text-xs"
                            >
                              Mahsup Et (Stok & Cari)
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
      )}

      {/* Sevk Etme Dialog */}
      <Dialog open={dispatchModalOpen} onOpenChange={setDispatchModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Sevkiyatı Başlat (SHP-#{selectedShipment?.id})</DialogTitle>
            <DialogDescription>
              Sigortalı zırhlı kargo veya kurye takip bilgilerini girin.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onDispatchSubmit)} className="flex flex-col gap-4 pt-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="shp-carrier">Taşıyıcı Firma</Label>
              <Input
                id="shp-carrier"
                placeholder="Örn: Loomis, Brinks, Yurtiçi Özel"
                disabled={isSubmitting}
                {...register("tasiyici")}
              />
              {errors.tasiyici && (
                <span className="text-[11px] text-destructive">
                  {errors.tasiyici.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="shp-tracking">Kargo Takip / İrsaliye No</Label>
              <Input
                id="shp-tracking"
                placeholder="Örn: LMS-2026-987654"
                disabled={isSubmitting}
                {...register("takip_no")}
              />
              {errors.takip_no && (
                <span className="text-[11px] text-destructive">
                  {errors.takip_no.message}
                </span>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setDispatchModalOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? "Kaydediliyor…" : "Sevk Et"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
