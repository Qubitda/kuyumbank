"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  useApproveReturnMutation,
  useCancelShipmentMutation,
  useDeliverShipmentMutation,
  useDispatchShipmentMutation,
  useMahsupReturnMutation,
  useOpsShipmentsQuery,
  usePrepareShipmentMutation,
  useReturnsQuery,
  useSubmitPodMutation,
} from "../hooks";
import {
  shipmentDispatchSchema,
  shipmentPodSchema,
  type ShipmentDispatchInput,
  type ShipmentPodInput,
} from "../schemas";
import type { OpsShipment } from "../types";
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
  Truck,
  RotateCcw,
  RefreshCw,
  AlertCircle,
  PackageCheck,
  Send,
  CheckCircle2,
  ClipboardCheck,
  Ban,
} from "lucide-react";

export function LogisticsManagementView() {
  const actionToast = useActionToast();
  const [activeTab, setActiveTab] = useState<"shipments" | "returns">(
    "shipments"
  );

  const shipmentsQ = useOpsShipmentsQuery();
  const returnsQ = useReturnsQuery();
  const prepareMut = usePrepareShipmentMutation();
  const dispatchMut = useDispatchShipmentMutation();
  const deliverMut = useDeliverShipmentMutation();
  const cancelMut = useCancelShipmentMutation();
  const podMut = useSubmitPodMutation();
  const approveMut = useApproveReturnMutation();
  const mahsupMut = useMahsupReturnMutation();

  const [dispatchModalOpen, setDispatchModalOpen] = useState(false);
  const [podModalOpen, setPodModalOpen] = useState(false);
  const [selectedShipment, setSelectedShipment] = useState<OpsShipment | null>(
    null
  );

  const dispatchForm = useForm<ShipmentDispatchInput>({
    resolver: zodResolver(shipmentDispatchSchema),
    defaultValues: { takip_no: "" },
  });

  const podForm = useForm<ShipmentPodInput>({
    resolver: zodResolver(shipmentPodSchema),
    defaultValues: { teslim_alan: "", notlar: "", belgeler_ref: "" },
  });

  const shipments = shipmentsQ.data ?? [];
  const returns = returnsQ.data ?? [];
  const loading = shipmentsQ.isLoading || returnsQ.isLoading;
  const error =
    shipmentsQ.isError && returnsQ.isError
      ? mapCommerceError(shipmentsQ.error, "Lojistik verileri alınamadı.")
      : null;

  const refetchAll = () => {
    void shipmentsQ.refetch();
    void returnsQ.refetch();
  };

  const runAction = async (label: string, fn: () => Promise<unknown>) => {
    try {
      await fn();
      actionToast.success(label);
    } catch (err) {
      actionToast.error(label, err);
    }
  };

  const onDispatchSubmit = async (formData: ShipmentDispatchInput) => {
    if (!selectedShipment) return;
    try {
      await dispatchMut.mutateAsync({
        id: selectedShipment.id,
        data: { takip_no: formData.takip_no },
      });
      actionToast.success("Sevk kaydedildi");
      setDispatchModalOpen(false);
      dispatchForm.reset();
    } catch (err) {
      actionToast.error("Sevk işlemi kaydedilemedi", err);
    }
  };

  const onPodSubmit = async (formData: ShipmentPodInput) => {
    if (!selectedShipment) return;
    try {
      await podMut.mutateAsync({
        id: selectedShipment.id,
        data: {
          teslim_alan: formData.teslim_alan,
          ...(formData.notlar ? { notlar: formData.notlar } : {}),
          ...(formData.belgeler_ref
            ? { belgeler_ref: formData.belgeler_ref }
            : {}),
        },
      });
      actionToast.success("POD kaydedildi");
      setPodModalOpen(false);
      podForm.reset();
    } catch (err) {
      actionToast.error("POD kaydedilemedi", err);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Lojistik & Sevkiyat Operasyonları
          </h1>
          <p className="text-xs text-muted-foreground">
            Dispatch yalnız `takip_no` (GAP-F4-01 tasiyici yok). POD ayrı endpoint.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refetchAll}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Yenile
          </Button>
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
              <span>İade ({returns.length})</span>
            </button>
          </div>
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
            onClick={refetchAll}
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
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shipments.map((s) => {
                  const actions = s.allowed_actions || [];
                  return (
                    <TableRow key={s.id}>
                      <TableCell className="font-mono text-xs font-semibold tabular-nums">
                        SHP-#{s.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs tabular-nums">
                        {s.order_id != null ? `Sipariş #${s.order_id}` : "—"}
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
                        <div className="flex items-center justify-end gap-1.5 flex-wrap">
                          {actions.includes("prepare") && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                void runAction("Hazırlık başlatıldı", () =>
                                  prepareMut.mutateAsync(s.id)
                                )
                              }
                              className="h-8 text-xs gap-1"
                            >
                              <PackageCheck className="h-3.5 w-3.5" />
                              Hazırla
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
                              Sevk Et
                            </Button>
                          )}
                          {actions.includes("pod") && (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => {
                                setSelectedShipment(s);
                                setPodModalOpen(true);
                              }}
                              className="h-8 text-xs gap-1"
                            >
                              <ClipboardCheck className="h-3.5 w-3.5" />
                              POD
                            </Button>
                          )}
                          {actions.includes("deliver") && (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() =>
                                void runAction("Teslim işaretlendi", () =>
                                  deliverMut.mutateAsync(s.id)
                                )
                              }
                              className="h-8 text-xs gap-1"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              Teslim
                            </Button>
                          )}
                          {actions.includes("cancel") && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                void runAction("Sevkiyat iptal", () =>
                                  cancelMut.mutateAsync(s.id)
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
      ) : (
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
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlem</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {returns.map((r) => {
                  const actions = r.allowed_actions || [];
                  return (
                    <TableRow key={r.id}>
                      <TableCell className="font-mono text-xs font-semibold tabular-nums">
                        RET-#{r.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs tabular-nums">
                        {r.order_id != null ? `Sipariş #${r.order_id}` : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            r.durum === "MAHSUP_EDILDI" ? "success" : "outline"
                          }
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
                              onClick={() =>
                                void runAction("İade onaylandı", () =>
                                  approveMut.mutateAsync(r.id)
                                )
                              }
                              className="h-8 text-xs"
                            >
                              Onayla
                            </Button>
                          )}
                          {actions.includes("mahsup") && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() =>
                                void runAction("İade mahsup edildi", () =>
                                  mahsupMut.mutateAsync(r.id)
                                )
                              }
                              className="h-8 text-xs"
                            >
                              Mahsup Et
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
          <p className="px-4 py-2 text-[11px] text-muted-foreground border-t border-border">
            İade sebep/mahsup tutarı OpenAPI’de yok (GAP-F4-04).
          </p>
        </div>
      )}

      <Dialog open={dispatchModalOpen} onOpenChange={setDispatchModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Sevk (SHP-#{selectedShipment?.id})</DialogTitle>
            <DialogDescription>
              OpenAPI `TakipNoRequest` — yalnız takip_no. Taşıyıcı alanı
              GAP-F4-01.
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={dispatchForm.handleSubmit(onDispatchSubmit)}
            className="flex flex-col gap-4 pt-2"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="shp-tracking">Kargo Takip / İrsaliye No</Label>
              <Input
                id="shp-tracking"
                placeholder="Örn: LMS-2026-987654"
                className="font-mono"
                disabled={dispatchForm.formState.isSubmitting}
                {...dispatchForm.register("takip_no")}
              />
              {dispatchForm.formState.errors.takip_no && (
                <span className="text-[11px] text-destructive">
                  {dispatchForm.formState.errors.takip_no.message}
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
              <Button
                type="submit"
                size="sm"
                disabled={
                  dispatchForm.formState.isSubmitting || dispatchMut.isPending
                }
              >
                Sevk Et
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={podModalOpen} onOpenChange={setPodModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>POD (SHP-#{selectedShipment?.id})</DialogTitle>
            <DialogDescription>
              `POST /ops/shipments/{"{id}"}/pod/` — teslim_alan zorunlu.
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={podForm.handleSubmit(onPodSubmit)}
            className="flex flex-col gap-4 pt-2"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="pod-alan">Teslim alan</Label>
              <Input
                id="pod-alan"
                disabled={podForm.formState.isSubmitting}
                {...podForm.register("teslim_alan")}
              />
              {podForm.formState.errors.teslim_alan && (
                <span className="text-[11px] text-destructive">
                  {podForm.formState.errors.teslim_alan.message}
                </span>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="pod-not">Notlar</Label>
              <Input
                id="pod-not"
                disabled={podForm.formState.isSubmitting}
                {...podForm.register("notlar")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="pod-ref">Belgeler ref</Label>
              <Input
                id="pod-ref"
                className="font-mono"
                disabled={podForm.formState.isSubmitting}
                {...podForm.register("belgeler_ref")}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPodModalOpen(false)}
              >
                İptal
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={podForm.formState.isSubmitting || podMut.isPending}
              >
                POD Kaydet
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
