"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { firmalarService } from "../services";
import {
  orgUnitSchema,
  inviteSchema,
  memberSchema,
  type OrgUnitInput,
  type InviteInput,
  type MemberInput,
} from "../schemas";
import type {
  Approval,
  FirmaAdresi,
  InviteItem,
  OrgMember,
  OrgUnit,
} from "../types";
import type { MeDashboard, MeResponse } from "@/lib/api/types";
import { formatMoney, formatDateTime } from "@/lib/format";
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
  Building2,
  CheckSquare,
  Users,
  Plus,
  RefreshCw,
  AlertCircle,
  Check,
  X,
  Mail,
  Send,
  CheckCircle2,
  Search,
  Eye,
  UserPlus,
} from "lucide-react";

const PAGE_SIZE = 10;

type TabId = "units" | "approvals" | "invites";
type StatusFilter = "all" | "active" | "passive";

function firmTypeLabel(firma: MeResponse["firma"]): string {
  if (!firma) return "—";
  const parts: string[] = [];
  if (firma.platform_mu) parts.push("Platform");
  if (firma.alici_mi) parts.push("Alıcı");
  if (firma.tedarikci_mi) parts.push("Tedarikçi");
  return parts.join(" · ") || "Firma";
}

export function FirmalarOrgView() {
  const [activeTab, setActiveTab] = useState<TabId>("units");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [dashboard, setDashboard] = useState<MeDashboard | null>(null);
  const [addresses, setAddresses] = useState<FirmaAdresi[]>([]);
  const [units, setUnits] = useState<OrgUnit[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [invites, setInvites] = useState<InviteItem[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [pageIndex, setPageIndex] = useState(0);

  const [createUnitOpen, setCreateUnitOpen] = useState(false);
  const [createInviteOpen, setCreateInviteOpen] = useState(false);
  const [detailUnit, setDetailUnit] = useState<OrgUnit | null>(null);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [addMemberOpen, setAddMemberOpen] = useState(false);

  const {
    register: registerUnit,
    handleSubmit: handleUnitSubmit,
    reset: resetUnit,
    formState: { errors: unitErrors, isSubmitting: isUnitSubmitting },
  } = useForm<OrgUnitInput>({
    resolver: zodResolver(orgUnitSchema),
    defaultValues: { kod: "", ad: "" },
  });

  const {
    register: registerInvite,
    handleSubmit: handleInviteSubmit,
    reset: resetInvite,
    formState: { errors: inviteErrors, isSubmitting: isInviteSubmitting },
  } = useForm<InviteInput>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { email: "", rol: "ALICI_SATINALMA" },
  });

  const {
    register: registerMember,
    handleSubmit: handleMemberSubmit,
    reset: resetMember,
    formState: { errors: memberErrors, isSubmitting: isMemberSubmitting },
  } = useForm<MemberInput>({
    resolver: zodResolver(memberSchema),
    defaultValues: { kullanici_id: 0 },
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [meRes, dashRes, unitsRes, approvalsRes, invitesRes, addrRes] =
        await Promise.allSettled([
          firmalarService.getMe(),
          firmalarService.getMeDashboard(),
          firmalarService.getOrgUnits(),
          firmalarService.getApprovals(),
          firmalarService.getInvites(),
          firmalarService.getAddresses(),
        ]);

      if (meRes.status === "fulfilled") setMe(meRes.value);
      if (dashRes.status === "fulfilled") setDashboard(dashRes.value);
      if (unitsRes.status === "fulfilled") setUnits(unitsRes.value.results || []);
      if (approvalsRes.status === "fulfilled") {
        setApprovals(approvalsRes.value.results || []);
      }
      if (invitesRes.status === "fulfilled") {
        setInvites(invitesRes.value.results || []);
      }
      if (addrRes.status === "fulfilled") {
        setAddresses(addrRes.value.results || []);
      }

      const hardFails = [meRes, unitsRes].filter((r) => r.status === "rejected");
      if (hardFails.length === 2) {
        const first = hardFails[0] as PromiseRejectedResult;
        setError(
          first.reason instanceof Error
            ? first.reason.message
            : "Firma verileri alınamadı."
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Firma verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  const pendingApprovals = useMemo(
    () => approvals.filter((a) => a.durum === "BEKLEMEDE").length,
    [approvals]
  );
  const activeUnits = useMemo(
    () => units.filter((u) => u.aktif !== false).length,
    [units]
  );
  const passiveUnits = useMemo(
    () => units.filter((u) => u.aktif === false).length,
    [units]
  );

  const filteredUnits = useMemo(() => {
    const q = query.trim().toLowerCase();
    return units.filter((u) => {
      if (statusFilter === "active" && u.aktif === false) return false;
      if (statusFilter === "passive" && u.aktif !== false) return false;
      if (!q) return true;
      return `${u.kod} ${u.ad} ${u.id}`.toLowerCase().includes(q);
    });
  }, [units, query, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredUnits.length / PAGE_SIZE));
  const safePage = Math.min(pageIndex, totalPages - 1);
  const pagedUnits = filteredUnits.slice(
    safePage * PAGE_SIZE,
    safePage * PAGE_SIZE + PAGE_SIZE
  );

  const primaryCity =
    addresses.find((a) => a.varsayilan)?.il || addresses[0]?.il || null;

  const onCreateUnitSubmit = async (formData: OrgUnitInput) => {
    setError(null);
    try {
      await firmalarService.createOrgUnit({
        kod: formData.kod,
        ad: formData.ad,
      });
      setCreateUnitOpen(false);
      resetUnit();
      setSuccessMsg("Organizasyon birimi oluşturuldu.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Birim oluşturulamadı.");
    }
  };

  const onCreateInviteSubmit = async (formData: InviteInput) => {
    setError(null);
    try {
      await firmalarService.createInvite({
        email: formData.email,
        rol: formData.rol,
      });
      setCreateInviteOpen(false);
      resetInvite();
      setSuccessMsg(`${formData.email} adresine davet gönderildi.`);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Davet gönderilemedi.");
    }
  };

  const openUnitDetail = async (unit: OrgUnit) => {
    setDetailUnit(unit);
    setMembersLoading(true);
    setMembers([]);
    try {
      const detail = await firmalarService.getOrgUnit(unit.id);
      setDetailUnit(detail);
      const mem = await firmalarService.getOrgMembers(unit.id);
      setMembers(mem.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Birim detayı alınamadı.");
    } finally {
      setMembersLoading(false);
    }
  };

  const onAddMemberSubmit = async (formData: MemberInput) => {
    if (!detailUnit) return;
    setError(null);
    try {
      await firmalarService.addOrgMember(detailUnit.id, {
        kullanici_id: Number(formData.kullanici_id),
      });
      setAddMemberOpen(false);
      resetMember();
      setSuccessMsg("Üye birime eklendi.");
      const mem = await firmalarService.getOrgMembers(detailUnit.id);
      setMembers(mem.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Üye eklenemedi.");
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await firmalarService.approveApproval(id);
      setSuccessMsg("Onay talebi onaylandı.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Onaylama başarısız.");
    }
  };

  const handleReject = async (id: number) => {
    try {
      await firmalarService.rejectApproval(id);
      setSuccessMsg("Onay talebi reddedildi.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reddetme başarısız.");
    }
  };

  const handleSubmitApproval = async (id: number) => {
    try {
      await firmalarService.submitApproval(id);
      setSuccessMsg("Onay talebi gönderildi.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gönderim başarısız.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 border-b border-border pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Firmalar
          </h1>
          <p className="text-xs text-muted-foreground max-w-[56ch] leading-relaxed">
            Tenant firma özeti, organizasyon birimleri, onaylar ve ekip davetleri.
            Çapraz firma listesi API’de yoktur; görünür firma oturum firmanızdır.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5 self-start"
          onClick={() => void fetchData()}
          disabled={loading}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Yenile
        </Button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Birim (toplam)" value={String(units.length)} />
        <Stat label="Aktif birim" value={String(activeUnits)} />
        <Stat label="Pasif birim" value={String(passiveUnits)} />
        <Stat label="Bekleyen onay" value={String(pendingApprovals)} />
      </div>

      {/* Tenant firma özeti — tek satırlık “firma listesi” */}
      <div className="rounded-[8px] border border-border bg-card overflow-hidden">
        <div className="border-b border-border px-4 py-3 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">Oturum Firması</h2>
        </div>
        {loading && !me ? (
          <div className="p-6 text-xs text-muted-foreground flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Firma bilgisi yükleniyor…
          </div>
        ) : !me?.firma ? (
          <div className="p-6 text-xs text-muted-foreground">
            Firma bilgisi bulunamadı.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Firma adı</TableHead>
                <TableHead>Firma kodu</TableHead>
                <TableHead>Tür</TableHead>
                <TableHead>Yetkili</TableHead>
                <TableHead>Şehir</TableHead>
                <TableHead>Durum</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium">{me.firma.ad}</TableCell>
                <TableCell className="font-mono text-xs">
                  {dashboard?.firma_kodu || `ID-${me.firma.id}`}
                </TableCell>
                <TableCell className="text-xs">{firmTypeLabel(me.firma)}</TableCell>
                <TableCell className="text-xs font-mono">{me.username}</TableCell>
                <TableCell className="text-xs">{primaryCity || "—"}</TableCell>
                <TableCell>
                  <Badge
                    variant={me.firma.aktif ? "success" : "secondary"}
                    className="font-mono text-[10px]"
                  >
                    {me.firma.aktif ? "AKTİF" : "PASİF"}
                  </Badge>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        )}
        <div className="border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          Vergi no / telefon / e-posta alanları bu uçta dönmüyor; profil ve adres
          bilgileri `/profil` ekranındadır.
        </div>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 rounded-[6px] border border-border bg-muted/60 p-3 text-xs text-foreground font-medium">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMsg}</span>
          <button
            type="button"
            className="ml-auto text-muted-foreground hover:text-foreground"
            onClick={() => setSuccessMsg(null)}
          >
            Kapat
          </button>
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
            onClick={() => void fetchData()}
            className="h-8 border-destructive/30"
          >
            Yeniden Dene
          </Button>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-1 rounded-[6px] border border-border bg-muted/40 p-1 w-fit">
        {(
          [
            ["units", "Birimler", units.length, Building2],
            ["approvals", "Onaylar", approvals.length, CheckSquare],
            ["invites", "Davetler", invites.length, Users],
          ] as const
        ).map(([id, label, count, Icon]) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 rounded-[4px] px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === id
                ? "bg-card text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            <span>
              {label} ({count})
            </span>
          </button>
        ))}
      </div>

      {loading && units.length === 0 && approvals.length === 0 ? (
        <div className="flex h-48 items-center justify-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Organizasyon verileri alınıyor…
        </div>
      ) : activeTab === "units" ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setPageIndex(0);
                  }}
                  placeholder="Kod veya ad ara…"
                  className="pl-8 h-9"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as StatusFilter);
                  setPageIndex(0);
                }}
                className="h-9 rounded-[6px] border border-border bg-background px-2 text-xs"
              >
                <option value="all">Tüm durumlar</option>
                <option value="active">Aktif</option>
                <option value="passive">Pasif</option>
              </select>
            </div>
            <Button size="sm" className="gap-1.5" onClick={() => setCreateUnitOpen(true)}>
              <Plus className="h-4 w-4" />
              Yeni birim
            </Button>
          </div>

          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            {filteredUnits.length === 0 ? (
              <div className="p-8 text-center text-xs text-muted-foreground">
                Organizasyon birimi bulunamadı.
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kod</TableHead>
                      <TableHead>Ad</TableHead>
                      <TableHead>Üst birim</TableHead>
                      <TableHead>Firma</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead className="text-right">İşlem</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pagedUnits.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-mono text-xs font-semibold">
                          {u.kod}
                        </TableCell>
                        <TableCell className="font-medium">{u.ad}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {u.parent_id ? `#${u.parent_id}` : "Kök"}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {u.firma_id != null ? `#${u.firma_id}` : "—"}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={u.aktif === false ? "secondary" : "success"}
                            className="font-mono text-[10px]"
                          >
                            {u.aktif === false ? "PASİF" : "AKTİF"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 gap-1.5 text-xs"
                            onClick={() => void openUnitDetail(u)}
                          >
                            <Eye className="h-3.5 w-3.5" />
                            Detay
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted-foreground">
                  <span>
                    {filteredUnits.length} kayıt · sayfa {safePage + 1}/{totalPages}
                  </span>
                  <div className="flex gap-2">
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
          </div>
        </div>
      ) : activeTab === "approvals" ? (
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          {approvals.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Onay talebi bulunamadı.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Sipariş</TableHead>
                  <TableHead className="text-right">Tutar</TableHead>
                  <TableHead>Gerekçe</TableHead>
                  <TableHead>Tarih</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.map((a) => {
                  const actions = a.allowed_actions || [];
                  return (
                    <TableRow key={a.id}>
                      <TableCell className="font-mono text-xs">#{a.id}</TableCell>
                      <TableCell className="font-mono text-xs">
                        {a.order_id != null ? `#${a.order_id}` : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums font-semibold">
                        {formatMoney(a.tutar, a.para_birimi || "TRY")}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">
                        {a.gerekce || "—"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {a.olusturma_tarihi
                          ? formatDateTime(a.olusturma_tarihi)
                          : "—"}
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
                        <div className="flex justify-end gap-1.5">
                          {actions.includes("submit") && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 text-xs"
                              onClick={() => void handleSubmitApproval(a.id)}
                            >
                              Gönder
                            </Button>
                          )}
                          {actions.includes("approve") && (
                            <Button
                              size="sm"
                              className="h-8 text-xs gap-1"
                              onClick={() => void handleApprove(a.id)}
                            >
                              <Check className="h-3.5 w-3.5" />
                              Onayla
                            </Button>
                          )}
                          {actions.includes("reject") && (
                            <Button
                              variant="destructive"
                              size="sm"
                              className="h-8 text-xs gap-1"
                              onClick={() => void handleReject(a.id)}
                            >
                              <X className="h-3.5 w-3.5" />
                              Reddet
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
        <div className="flex flex-col gap-4">
          <div className="flex justify-end">
            <Button
              size="sm"
              className="gap-1.5"
              onClick={() => setCreateInviteOpen(true)}
            >
              <Mail className="h-4 w-4" />
              Davet gönder
            </Button>
          </div>
          <div className="rounded-[8px] border border-border bg-card overflow-hidden">
            {invites.length === 0 ? (
              <div className="p-8 text-center text-xs text-muted-foreground">
                Davet kaydı bulunamadı.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>E-posta</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Firma</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead>Son geçerlilik</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invites.map((inv) => (
                    <TableRow key={inv.id}>
                      <TableCell className="font-medium">{inv.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px]">
                          {inv.rol}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {inv.firma_id != null ? `#${inv.firma_id}` : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={inv.expired ? "destructive" : "secondary"}
                          className="font-mono text-[10px]"
                        >
                          {inv.expired
                            ? "SURESI_DOLDU"
                            : inv.durum || "BEKLEMEDE"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {inv.expires_at ? formatDateTime(inv.expires_at) : "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </div>
      )}

      {/* Create unit */}
      <Dialog open={createUnitOpen} onOpenChange={setCreateUnitOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Yeni organizasyon birimi</DialogTitle>
            <DialogDescription>
              `POST /org-units/` — kod zorunlu.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={handleUnitSubmit(onCreateUnitSubmit)}
            className="flex flex-col gap-4 pt-2"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="unit-kod">Birim kodu</Label>
              <Input id="unit-kod" disabled={isUnitSubmitting} {...registerUnit("kod")} />
              {unitErrors.kod && (
                <span className="text-[11px] text-destructive">
                  {unitErrors.kod.message}
                </span>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="unit-ad">Birim adı</Label>
              <Input id="unit-ad" disabled={isUnitSubmitting} {...registerUnit("ad")} />
              {unitErrors.ad && (
                <span className="text-[11px] text-destructive">
                  {unitErrors.ad.message}
                </span>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCreateUnitOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isUnitSubmitting}>
                {isUnitSubmitting ? "Kaydediliyor…" : "Kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Invite */}
      <Dialog open={createInviteOpen} onOpenChange={setCreateInviteOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Ekip daveti</DialogTitle>
            <DialogDescription>
              `POST /auth/invites/create/` — email + rol.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={handleInviteSubmit(onCreateInviteSubmit)}
            className="flex flex-col gap-4 pt-2"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="inv-email">E-posta</Label>
              <Input
                id="inv-email"
                type="email"
                disabled={isInviteSubmitting}
                {...registerInvite("email")}
              />
              {inviteErrors.email && (
                <span className="text-[11px] text-destructive">
                  {inviteErrors.email.message}
                </span>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="inv-role">Rol</Label>
              <select
                id="inv-role"
                className="h-9 w-full rounded-[6px] border border-border bg-background px-3 text-xs"
                disabled={isInviteSubmitting}
                {...registerInvite("rol")}
              >
                <option value="ALICI_SATINALMA">ALICI_SATINALMA</option>
                <option value="ALICI_FINANS">ALICI_FINANS</option>
                <option value="ALICI_YONETICI">ALICI_YONETICI</option>
                <option value="TEDARIKCI_SATIS">TEDARIKCI_SATIS</option>
                <option value="TEDARIKCI_ATOLYE">TEDARIKCI_ATOLYE</option>
                <option value="TEDARIKCI_YONETICI">TEDARIKCI_YONETICI</option>
              </select>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCreateInviteOpen(false)}
              >
                İptal
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={isInviteSubmitting}
                className="gap-1.5"
              >
                <Send className="h-3.5 w-3.5" />
                {isInviteSubmitting ? "Gönderiliyor…" : "Gönder"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Unit detail + members */}
      <Dialog
        open={Boolean(detailUnit)}
        onOpenChange={(open) => {
          if (!open) {
            setDetailUnit(null);
            setMembers([]);
            setAddMemberOpen(false);
          }
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Birim detayı</DialogTitle>
            <DialogDescription>
              `GET /org-units/{"{id}"}/` ve üyeler.
            </DialogDescription>
          </DialogHeader>
          {detailUnit && (
            <div className="flex flex-col gap-4 pt-1">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <Detail label="ID" value={`#${detailUnit.id}`} />
                <Detail label="Kod" value={detailUnit.kod} mono />
                <Detail label="Ad" value={detailUnit.ad} />
                <Detail
                  label="Durum"
                  value={detailUnit.aktif === false ? "PASİF" : "AKTİF"}
                />
                <Detail
                  label="Üst birim"
                  value={detailUnit.parent_id != null ? `#${detailUnit.parent_id}` : "Kök"}
                />
                <Detail
                  label="Firma"
                  value={
                    detailUnit.firma_id != null ? `#${detailUnit.firma_id}` : "—"
                  }
                  mono
                />
              </div>

              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-foreground">Üyeler</h3>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8 gap-1.5 text-xs"
                  onClick={() => setAddMemberOpen(true)}
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  Üye ekle
                </Button>
              </div>

              {membersLoading ? (
                <div className="text-xs text-muted-foreground flex items-center gap-2">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Üyeler yükleniyor…
                </div>
              ) : members.length === 0 ? (
                <div className="text-xs text-muted-foreground">Üye bulunamadı.</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Üyelik</TableHead>
                      <TableHead>Kullanıcı</TableHead>
                      <TableHead>Tarih</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {members.map((m) => (
                      <TableRow key={m.id}>
                        <TableCell className="font-mono text-xs">#{m.id}</TableCell>
                        <TableCell className="font-mono text-xs">
                          #{m.kullanici_id}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {m.olusturma_tarihi
                            ? formatDateTime(m.olusturma_tarihi)
                            : "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}

              {addMemberOpen && (
                <form
                  onSubmit={handleMemberSubmit(onAddMemberSubmit)}
                  className="flex flex-col gap-3 border-t border-border pt-3"
                >
                  <Label htmlFor="member-uid">Kullanıcı id</Label>
                  <Input
                    id="member-uid"
                    type="number"
                    className="font-mono"
                    disabled={isMemberSubmitting}
                    {...registerMember("kullanici_id", { valueAsNumber: true })}
                  />
                  {memberErrors.kullanici_id && (
                    <span className="text-[11px] text-destructive">
                      {memberErrors.kullanici_id.message}
                    </span>
                  )}
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setAddMemberOpen(false)}
                    >
                      İptal
                    </Button>
                    <Button type="submit" size="sm" disabled={isMemberSubmitting}>
                      {isMemberSubmitting ? "Ekleniyor…" : "Ekle"}
                    </Button>
                  </div>
                </form>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
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

function Detail({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-[6px] border border-border px-2.5 py-2">
      <div className="text-[10px] text-muted-foreground">{label}</div>
      <div className={`text-xs text-foreground ${mono ? "font-mono" : "font-medium"}`}>
        {value}
      </div>
    </div>
  );
}
