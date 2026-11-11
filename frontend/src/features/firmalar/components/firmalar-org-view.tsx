"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { firmalarService } from "../services";
import { orgUnitSchema, type OrgUnitInput } from "../schemas";
import type { OrgUnit, Approval } from "../types";
import { formatMoney } from "@/lib/format";
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
import { Building2, CheckSquare, Plus, RefreshCw, AlertCircle, Check, X } from "lucide-react";

export function FirmalarOrgView() {
  const [activeTab, setActiveTab] = useState<"units" | "approvals">("units");

  const [units, setUnits] = useState<OrgUnit[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [createUnitOpen, setCreateUnitOpen] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<OrgUnitInput>({
    resolver: zodResolver(orgUnitSchema),
    defaultValues: {
      kod: "",
      ad: "",
    },
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [unitsRes, approvalsRes] = await Promise.allSettled([
        firmalarService.getOrgUnits(),
        firmalarService.getApprovals(),
      ]);

      if (unitsRes.status === "fulfilled") {
        setUnits(unitsRes.value?.results || []);
      }
      if (approvalsRes.status === "fulfilled") {
        setApprovals(approvalsRes.value?.results || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Organizasyon verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onCreateUnitSubmit = async (formData: OrgUnitInput) => {
    try {
      await firmalarService.createOrgUnit({
        kod: formData.kod,
        ad: formData.ad,
      });
      setCreateUnitOpen(false);
      reset();
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Organizasyon birimi oluşturulamadı.");
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await firmalarService.approveApproval(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Onaylama işlemi başarısız.");
    }
  };

  const handleReject = async (id: number) => {
    try {
      await firmalarService.rejectApproval(id);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reddetme işlemi başarısız.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık ve Sekmeler */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Firmalar & Organizasyon
          </h1>
          <p className="text-xs text-muted-foreground">
            Birim hiyerarşisi, şubeler ve sipariş harcama onay mekanizması (Approvals).
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-[6px] border border-border bg-muted/40 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("units")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "units"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Building2 className="h-3.5 w-3.5" />
            <span>Organizasyon Birimleri ({units.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("approvals")}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === "approvals"
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <CheckSquare className="h-3.5 w-3.5" />
            <span>Onay Talepleri ({approvals.length})</span>
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
            <span>Veriler alınıyor…</span>
          </div>
        </div>
      ) : activeTab === "units" ? (
        /* OrgUnits Tablosu */
        <div className="flex flex-col gap-4">
          <div className="flex justify-end">
            <Button
              size="sm"
              onClick={() => setCreateUnitOpen(true)}
              className="gap-1.5"
            >
              <Plus className="h-4 w-4" />
              <span>Yeni Birim / Şube Ekle</span>
            </Button>
          </div>

          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            {units.length === 0 ? (
              <div className="p-8 text-center text-xs text-muted-foreground">
                Tanımlı organizasyon birimi bulunamadı.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">Birim Kodu</TableHead>
                    <TableHead>Birim Adı</TableHead>
                    <TableHead>Üst Birim</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {units.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell className="font-mono text-xs font-semibold">
                        {u.kod}
                      </TableCell>
                      <TableCell className="font-medium text-foreground">
                        {u.ad}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {u.parent_id ? `Birim #${u.parent_id}` : "Ana Birim (Kök)"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </div>
      ) : (
        /* Approvals Tablosu */
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          {approvals.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Bekleyen onay talebi bulunmamaktadır.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Onay ID</TableHead>
                  <TableHead>Sipariş Ref</TableHead>
                  <TableHead className="text-right">Talep Tutarı</TableHead>
                  <TableHead>Gerekçe</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.map((a) => {
                  const actions = a.allowed_actions || [];
                  return (
                    <TableRow key={a.id}>
                      <TableCell className="font-mono text-xs font-semibold">
                        APR-#{a.id}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {a.order_id ? `Sipariş #${a.order_id}` : "Genel Harcama"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums font-semibold text-foreground">
                        {formatMoney(a.tutar, a.para_birimi || "TRY")}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-xs truncate">
                        {a.gerekce || "—"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            a.durum === "ONAYLANDI"
                              ? "success"
                              : a.durum === "REDDEDILDI"
                              ? "destructive"
                              : "warning"
                          }
                          className="font-mono text-[10px]"
                        >
                          {a.durum}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {actions.includes("approve") && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => handleApprove(a.id)}
                              className="h-8 text-xs gap-1"
                            >
                              <Check className="h-3.5 w-3.5" />
                              <span>Onayla</span>
                            </Button>
                          )}
                          {actions.includes("reject") && (
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleReject(a.id)}
                              className="h-8 text-xs gap-1"
                            >
                              <X className="h-3.5 w-3.5" />
                              <span>Reddet</span>
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

      {/* Yeni Birim Ekleme Dialog */}
      <Dialog open={createUnitOpen} onOpenChange={setCreateUnitOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Yeni Organizasyon Birimi / Şube</DialogTitle>
            <DialogDescription>
              Firma içi departman veya şube tanımı oluşturur.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onCreateUnitSubmit)} className="flex flex-col gap-4 pt-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="unit-kod">Birim Kodu</Label>
              <Input
                id="unit-kod"
                placeholder="Örn: IST-MERKEZ veya SUBE-01"
                disabled={isSubmitting}
                {...register("kod")}
              />
              {errors.kod && (
                <span className="text-[11px] text-destructive">
                  {errors.kod.message}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="unit-ad">Birim Adı</Label>
              <Input
                id="unit-ad"
                placeholder="Örn: Kapalıçarşı Ana Toptan Şubesi"
                disabled={isSubmitting}
                {...register("ad")}
              />
              {errors.ad && (
                <span className="text-[11px] text-destructive">
                  {errors.ad.message}
                </span>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCreateUnitOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? "Kaydediliyor…" : "Kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
