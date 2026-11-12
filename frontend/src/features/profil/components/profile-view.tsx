"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/features/auth";
import { useTheme } from "@/components/layout";
import { profilService } from "../services";
import {
  profileSchema,
  passwordChangeSchema,
  addressSchema,
  emailVerifyConfirmSchema,
  type ProfileInput,
  type PasswordChangeInput,
  type AddressInput,
  type EmailVerifyConfirmInput,
} from "../schemas";
import type { FirmaAdresi, MeProfile } from "../types";
import type { MeDashboard } from "@/lib/api/types";
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
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import {
  User,
  Shield,
  MapPin,
  Building2,
  Settings,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Plus,
  Trash2,
  Mail,
  LogOut,
  ArrowRight,
} from "lucide-react";

type TabId = "personal" | "security" | "addresses" | "firma" | "prefs";

function firmTypeLabel(firma: MeProfile["firma"]): string {
  if (!firma) return "—";
  const parts: string[] = [];
  if (firma.platform_mu) parts.push("Platform");
  if (firma.alici_mi) parts.push("Alıcı");
  if (firma.tedarikci_mi) parts.push("Tedarikçi");
  return parts.join(" · ") || "Firma";
}

function initials(profile: MeProfile | null): string {
  if (!profile) return "?";
  const a = (profile.first_name || "").trim().charAt(0);
  const b = (profile.last_name || "").trim().charAt(0);
  const s = `${a}${b}`.toUpperCase();
  return s || profile.username.charAt(0).toUpperCase() || "?";
}

export function ProfileView() {
  const { user, logout, refresh } = useAuth();
  const { theme, setTheme } = useTheme();

  const [tab, setTab] = useState<TabId>("personal");
  const [profile, setProfile] = useState<MeProfile | null>(null);
  const [dashboard, setDashboard] = useState<MeDashboard | null>(null);
  const [addresses, setAddresses] = useState<FirmaAdresi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [addressModalOpen, setAddressModalOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const {
    register: registerProfile,
    handleSubmit: handleProfileSubmit,
    reset: resetProfile,
    formState: { errors: profileErrors, isSubmitting: isProfileSubmitting, isDirty },
  } = useForm<ProfileInput>({
    resolver: zodResolver(profileSchema),
    defaultValues: { first_name: "", last_name: "" },
  });

  const {
    register: registerPassword,
    handleSubmit: handlePasswordSubmit,
    reset: resetPassword,
    formState: { errors: passwordErrors, isSubmitting: isPasswordSubmitting },
  } = useForm<PasswordChangeInput>({
    resolver: zodResolver(passwordChangeSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      new_password_confirm: "",
    },
  });

  const {
    register: registerAddress,
    handleSubmit: handleAddressSubmit,
    reset: resetAddress,
    formState: { errors: addressErrors, isSubmitting: isAddressSubmitting },
  } = useForm<AddressInput>({
    resolver: zodResolver(addressSchema),
    defaultValues: {
      tip: "TESLIMAT",
      il: "",
      ilce: "",
      adres: "",
      varsayilan: true,
    },
  });

  const {
    register: registerVerify,
    handleSubmit: handleVerifySubmit,
    reset: resetVerify,
    formState: { errors: verifyErrors, isSubmitting: isVerifySubmitting },
  } = useForm<EmailVerifyConfirmInput>({
    resolver: zodResolver(emailVerifyConfirmSchema),
    defaultValues: { uid: "", token: "" },
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profileRes, addrRes, dashRes] = await Promise.allSettled([
        profilService.getProfile(),
        profilService.getAddresses(),
        profilService.getMeDashboard(),
      ]);

      if (profileRes.status === "fulfilled") {
        setProfile(profileRes.value);
        resetProfile({
          first_name: profileRes.value.first_name || "",
          last_name: profileRes.value.last_name || "",
        });
        setEditing(false);
      } else {
        setError(
          profileRes.reason instanceof Error
            ? profileRes.reason.message
            : "Profil alınamadı."
        );
      }
      if (addrRes.status === "fulfilled") {
        setAddresses(addrRes.value.results || []);
      }
      if (dashRes.status === "fulfilled") setDashboard(dashRes.value);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profil yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  const caps = useMemo(() => {
    if (!user?.capabilities) return [];
    return Object.entries(user.capabilities)
      .filter(([, v]) => Boolean(v))
      .map(([k]) => k);
  }, [user]);

  const onProfileSave = async (data: ProfileInput) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await profilService.updateProfile({
        first_name: data.first_name,
        last_name: data.last_name,
      });
      setProfile(updated);
      resetProfile({
        first_name: updated.first_name || "",
        last_name: updated.last_name || "",
      });
      setEditing(false);
      setSuccessMsg("Profil güncellendi.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profil kaydedilemedi.");
    }
  };

  const cancelEdit = () => {
    if (!profile) return;
    resetProfile({
      first_name: profile.first_name || "",
      last_name: profile.last_name || "",
    });
    setEditing(false);
  };

  const onPasswordSave = async (data: PasswordChangeInput) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await profilService.changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
        new_password_confirm: data.new_password_confirm,
      });
      resetPassword();
      setSuccessMsg(res.detail || "Şifre değiştirildi.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Şifre değiştirilemedi.");
    }
  };

  const onRequestEmailVerify = async () => {
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await profilService.requestEmailVerify();
      setSuccessMsg(res.detail || "Doğrulama e-postası gönderildi.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Doğrulama isteği gönderilemedi."
      );
    }
  };

  const onConfirmEmailVerify = async (data: EmailVerifyConfirmInput) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await profilService.confirmEmailVerify(data);
      setSuccessMsg(res.detail || "E-posta doğrulandı.");
      resetVerify();
      await fetchData();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Doğrulama başarısız.");
    }
  };

  const onAddressSave = async (data: AddressInput) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await profilService.createAddress({
        tip: data.tip,
        il: data.il,
        ilce: data.ilce,
        adres: data.adres,
        varsayilan: data.varsayilan,
      });
      setAddressModalOpen(false);
      resetAddress();
      setSuccessMsg("Adres kaydedildi.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Adres kaydedilemedi.");
    }
  };

  const onDeleteAddress = async (id: number) => {
    setError(null);
    try {
      await profilService.deleteAddress(id);
      setSuccessMsg("Adres silindi.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Adres silinemedi.");
    }
  };

  const onLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
    } finally {
      setLoggingOut(false);
    }
  };

  const tabs: Array<{ id: TabId; label: string; icon: typeof User }> = [
    { id: "personal", label: "Kişisel", icon: User },
    { id: "security", label: "Güvenlik", icon: Shield },
    { id: "addresses", label: "Adresler", icon: MapPin },
    { id: "firma", label: "Firma", icon: Building2 },
    { id: "prefs", label: "Tercihler", icon: Settings },
  ];

  return (
    <div className="flex flex-col gap-6 max-w-[1000px]">
      <div className="flex flex-col gap-1 border-b border-border pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Profil
          </h1>
          <p className="text-xs text-muted-foreground">
            Hesap bilgileri, güvenlik ve firma adresleri — yalnızca kendi
            oturumunuz.
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

      {successMsg && (
        <div className="flex items-center gap-2 rounded-[6px] border border-border bg-muted/60 p-3 text-xs font-medium">
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
          className="flex items-center justify-between rounded-[8px] border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="h-8"
            onClick={() => void fetchData()}
          >
            Yeniden dene
          </Button>
        </div>
      )}

      {loading && !profile ? (
        <div className="flex h-40 items-center justify-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Profil yükleniyor…
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6">
          {/* Sol özet */}
          <aside className="rounded-[8px] border border-border bg-card p-5 space-y-4 h-fit">
            <div className="flex flex-col items-center gap-3 text-center">
              <div
                className="flex h-16 w-16 items-center justify-center rounded-full border border-border bg-muted font-mono text-lg font-semibold text-foreground"
                aria-hidden
              >
                {initials(profile)}
              </div>
              <div className="space-y-0.5">
                <div className="text-sm font-semibold text-foreground">
                  {[profile?.first_name, profile?.last_name]
                    .filter(Boolean)
                    .join(" ") || profile?.username || "—"}
                </div>
                <div className="text-[11px] font-mono text-muted-foreground">
                  @{profile?.username}
                </div>
              </div>
              {profile?.rol ? (
                <Badge variant="outline" className="font-mono text-[10px]">
                  {profile.rol}
                </Badge>
              ) : null}
            </div>

            <div className="space-y-2 border-t border-border pt-3 text-xs">
              <Row label="E-posta" value={profile?.email || "—"} />
              <Row
                label="Doğrulama"
                value={
                  profile?.email_verified ? (
                    <Badge variant="success" className="font-mono text-[10px]">
                      DOĞRULANDI
                    </Badge>
                  ) : (
                    <Badge variant="warning" className="font-mono text-[10px]">
                      BEKLIYOR
                    </Badge>
                  )
                }
              />
              <Row
                label="Firma"
                value={profile?.firma?.ad || "—"}
              />
              <Row
                label="Durum"
                value={
                  profile?.firma ? (
                    <Badge
                      variant={profile.firma.aktif ? "success" : "secondary"}
                      className="font-mono text-[10px]"
                    >
                      {profile.firma.aktif ? "AKTİF" : "PASİF"}
                    </Badge>
                  ) : (
                    "—"
                  )
                }
              />
            </div>

            <p className="text-[10px] text-muted-foreground leading-relaxed border-t border-border pt-3">
              Profil fotoğrafı, telefon, kayıt/son giriş tarihi ve oturum listesi
              bu API’de yok; yükleme veya sahte alan eklenmez.
            </p>

            <nav className="flex flex-col gap-1 border-t border-border pt-3">
              {tabs.map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTab(t.id)}
                    className={`flex items-center gap-2 rounded-[6px] px-2.5 py-2 text-xs font-medium transition-colors text-left ${
                      tab === t.id
                        ? "bg-secondary text-foreground"
                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {t.label}
                  </button>
                );
              })}
            </nav>
          </aside>

          {/* Sağ içerik */}
          <div className="min-w-0 space-y-4">
            {tab === "personal" && (
              <section className="rounded-[8px] border border-border bg-card p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <h2 className="text-sm font-semibold">Kişisel bilgiler</h2>
                  {!editing ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditing(true)}
                    >
                      Düzenle
                    </Button>
                  ) : null}
                </div>

                <form
                  onSubmit={handleProfileSubmit(onProfileSave)}
                  className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                >
                  <Field label="Ad" error={profileErrors.first_name?.message}>
                    <Input
                      disabled={!editing || isProfileSubmitting}
                      {...registerProfile("first_name")}
                    />
                  </Field>
                  <Field label="Soyad" error={profileErrors.last_name?.message}>
                    <Input
                      disabled={!editing || isProfileSubmitting}
                      {...registerProfile("last_name")}
                    />
                  </Field>
                  <Field label="Kullanıcı adı">
                    <Input value={profile?.username || ""} disabled readOnly className="font-mono" />
                  </Field>
                  <Field label="E-posta">
                    <Input value={profile?.email || ""} disabled readOnly />
                  </Field>
                  <Field label="Rol">
                    <Input value={profile?.rol || ""} disabled readOnly className="font-mono" />
                  </Field>

                  {editing ? (
                    <div className="sm:col-span-2 flex justify-end gap-2 pt-1">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={cancelEdit}
                        disabled={isProfileSubmitting}
                      >
                        İptal
                      </Button>
                      <Button
                        type="submit"
                        size="sm"
                        disabled={isProfileSubmitting || !isDirty}
                      >
                        {isProfileSubmitting ? "Kaydediliyor…" : "Kaydet"}
                      </Button>
                    </div>
                  ) : null}
                </form>

                <div className="border-t border-border pt-4 space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-medium">E-posta doğrulama</div>
                      <p className="text-[11px] text-muted-foreground">
                        PATCH e-posta kabul etmez. Doğrulama için{" "}
                        <code className="font-mono">/auth/email-verify/</code>.
                      </p>
                    </div>
                    {!profile?.email_verified ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 shrink-0"
                        onClick={() => void onRequestEmailVerify()}
                      >
                        <Mail className="h-3.5 w-3.5" />
                        Doğrulama gönder
                      </Button>
                    ) : (
                      <Badge variant="success" className="font-mono text-[10px]">
                        DOĞRULANDI
                      </Badge>
                    )}
                  </div>
                </div>
              </section>
            )}

            {tab === "security" && (
              <section className="rounded-[8px] border border-border bg-card p-5 space-y-5">
                <div className="border-b border-border pb-3 space-y-1">
                  <h2 className="text-sm font-semibold">Şifre değiştir</h2>
                  <p className="text-[11px] text-muted-foreground">
                    En az 8 karakter, harf ve rakam. Şifreler saklanmaz veya
                    loglanmaz.
                  </p>
                </div>

                <form
                  onSubmit={handlePasswordSubmit(onPasswordSave)}
                  className="flex flex-col gap-4 max-w-md"
                >
                  <PasswordField
                    id="cur-pw"
                    label="Mevcut şifre"
                    show={showCurrent}
                    onToggle={() => setShowCurrent((v) => !v)}
                    error={passwordErrors.current_password?.message}
                    disabled={isPasswordSubmitting}
                    autoComplete="current-password"
                    {...registerPassword("current_password")}
                  />
                  <PasswordField
                    id="new-pw"
                    label="Yeni şifre"
                    show={showNew}
                    onToggle={() => setShowNew((v) => !v)}
                    error={passwordErrors.new_password?.message}
                    disabled={isPasswordSubmitting}
                    autoComplete="new-password"
                    {...registerPassword("new_password")}
                  />
                  <PasswordField
                    id="new-pw2"
                    label="Yeni şifre (tekrar)"
                    show={showConfirm}
                    onToggle={() => setShowConfirm((v) => !v)}
                    error={passwordErrors.new_password_confirm?.message}
                    disabled={isPasswordSubmitting}
                    autoComplete="new-password"
                    {...registerPassword("new_password_confirm")}
                  />
                  <ul className="text-[11px] text-muted-foreground space-y-0.5 list-disc pl-4">
                    <li>Minimum 8 karakter</li>
                    <li>En az bir harf ve bir rakam</li>
                    <li>Mevcut şifreden farklı olmalı</li>
                  </ul>
                  <div className="flex justify-end">
                    <Button type="submit" size="sm" disabled={isPasswordSubmitting}>
                      {isPasswordSubmitting ? "Değiştiriliyor…" : "Şifreyi değiştir"}
                    </Button>
                  </div>
                </form>

                {!profile?.email_verified ? (
                  <div className="border-t border-border pt-4 space-y-3">
                    <h3 className="text-xs font-semibold">E-posta doğrulama onayı</h3>
                    <p className="text-[11px] text-muted-foreground">
                      Postadaki uid / token ile onaylayın.
                    </p>
                    <form
                      onSubmit={handleVerifySubmit(onConfirmEmailVerify)}
                      className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg"
                    >
                      <Field label="uid" error={verifyErrors.uid?.message}>
                        <Input
                          className="font-mono"
                          disabled={isVerifySubmitting}
                          {...registerVerify("uid")}
                        />
                      </Field>
                      <Field label="token" error={verifyErrors.token?.message}>
                        <Input
                          className="font-mono"
                          disabled={isVerifySubmitting}
                          {...registerVerify("token")}
                        />
                      </Field>
                      <div className="sm:col-span-2 flex justify-end">
                        <Button
                          type="submit"
                          size="sm"
                          variant="outline"
                          disabled={isVerifySubmitting}
                        >
                          {isVerifySubmitting ? "Onaylanıyor…" : "Doğrulamayı onayla"}
                        </Button>
                      </div>
                    </form>
                  </div>
                ) : null}

                <div className="border-t border-border pt-4 space-y-2">
                  <h3 className="text-xs font-semibold">Oturum</h3>
                  <p className="text-[11px] text-muted-foreground">
                    Cihaz/oturum listesi endpoint’i yok. Mevcut oturumu kapatmak
                    için logout kullanın.
                  </p>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="gap-1.5"
                    disabled={loggingOut}
                    onClick={() => void onLogout()}
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    {loggingOut ? "Çıkış yapılıyor…" : "Oturumu kapat"}
                  </Button>
                </div>
              </section>
            )}

            {tab === "addresses" && (
              <section className="space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold">Firma adresleri</h2>
                  <Button
                    size="sm"
                    variant="outline"
                    className="gap-1.5"
                    onClick={() => setAddressModalOpen(true)}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Yeni adres
                  </Button>
                </div>
                <div className="rounded-[8px] border border-border bg-card overflow-hidden">
                  {addresses.length === 0 ? (
                    <p className="p-6 text-xs text-muted-foreground text-center">
                      Kayıtlı adres yok.
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Tip</TableHead>
                          <TableHead>İl / İlçe</TableHead>
                          <TableHead>Adres</TableHead>
                          <TableHead>Varsayılan</TableHead>
                          <TableHead className="text-right">İşlem</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {addresses.map((a) => (
                          <TableRow key={a.id}>
                            <TableCell>
                              <Badge
                                variant={
                                  a.tip === "TESLIMAT" ? "default" : "secondary"
                                }
                                className="font-mono text-[10px]"
                              >
                                {a.tip}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-xs font-medium">
                              {a.il}
                              {a.ilce ? ` / ${a.ilce}` : ""}
                            </TableCell>
                            <TableCell className="text-xs text-muted-foreground max-w-[220px] truncate">
                              {a.adres}
                            </TableCell>
                            <TableCell>
                              {a.varsayilan ? (
                                <Badge
                                  variant="outline"
                                  className="font-mono text-[10px]"
                                >
                                  VARSAYILAN
                                </Badge>
                              ) : (
                                "—"
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive"
                                onClick={() => void onDeleteAddress(a.id)}
                                aria-label="Adresi sil"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>
              </section>
            )}

            {tab === "firma" && (
              <section className="rounded-[8px] border border-border bg-card p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <h2 className="text-sm font-semibold">Bağlı firma</h2>
                  <Link
                    href="/firmalar"
                    className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
                  >
                    Firma yönetimi <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
                {!profile?.firma ? (
                  <p className="text-xs text-muted-foreground">Firma bilgisi yok.</p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <Info label="Firma adı" value={profile.firma.ad} />
                    <Info
                      label="Firma kodu"
                      value={dashboard?.firma_kodu || `ID-${profile.firma.id}`}
                      mono
                    />
                    <Info label="Tür" value={firmTypeLabel(profile.firma)} />
                    <Info label="Rolünüz" value={profile.rol} mono />
                    <Info
                      label="Firma durumu"
                      value={profile.firma.aktif ? "AKTİF" : "PASİF"}
                    />
                    <Info
                      label="Üyelik"
                      value={profile.firma.aktif ? "Aktif üye" : "Pasif"}
                    />
                  </div>
                )}

                <div className="border-t border-border pt-4 space-y-2">
                  <h3 className="text-xs font-semibold">Yetkiler (capabilities)</h3>
                  {caps.length === 0 ? (
                    <p className="text-[11px] text-muted-foreground">
                      Capability bilgisi yok.
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {caps.map((c) => (
                        <Badge
                          key={c}
                          variant="outline"
                          className="font-mono text-[10px]"
                        >
                          {c}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </section>
            )}

            {tab === "prefs" && (
              <section className="rounded-[8px] border border-border bg-card p-5 space-y-4">
                <div className="border-b border-border pb-3 space-y-1">
                  <h2 className="text-sm font-semibold">Hesap tercihleri</h2>
                  <p className="text-[11px] text-muted-foreground">
                    Görünüm tercihi tarayıcıda saklanır. Dil/saat dilimi ve
                    bildirim tercihleri için backend endpoint yok.
                  </p>
                </div>

                <div className="space-y-2 max-w-sm">
                  <Label htmlFor="theme-pref">Görünüm</Label>
                  <select
                    id="theme-pref"
                    className="h-9 w-full rounded-[6px] border border-border bg-background px-3 text-xs"
                    value={theme}
                    onChange={(e) =>
                      setTheme(e.target.value as "light" | "dark" | "system")
                    }
                  >
                    <option value="light">Açık</option>
                    <option value="dark">Koyu</option>
                    <option value="system">Sistem</option>
                  </select>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs border-t border-border pt-4">
                  <Info label="Dil" value="tr-TR (sabit)" />
                  <Info label="Saat dilimi" value="Europe/Istanbul (sabit)" />
                  <Info label="Para birimi gösterimi" value="TRY · tabular-nums" />
                </div>
              </section>
            )}
          </div>
        </div>
      )}

      <Dialog open={addressModalOpen} onOpenChange={setAddressModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Yeni adres</DialogTitle>
            <DialogDescription>
              Teslimat veya fatura adresi (`POST /me/addresses/`).
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={handleAddressSubmit(onAddressSave)}
            className="flex flex-col gap-4 pt-2"
          >
            <Field label="Adres türü" error={addressErrors.tip?.message}>
              <select
                className="h-9 w-full rounded-[6px] border border-border bg-background px-3 text-xs"
                disabled={isAddressSubmitting}
                {...registerAddress("tip")}
              >
                <option value="TESLIMAT">TESLIMAT</option>
                <option value="FATURA">FATURA</option>
              </select>
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="İl" error={addressErrors.il?.message}>
                <Input disabled={isAddressSubmitting} {...registerAddress("il")} />
              </Field>
              <Field label="İlçe">
                <Input disabled={isAddressSubmitting} {...registerAddress("ilce")} />
              </Field>
            </div>
            <Field label="Açık adres" error={addressErrors.adres?.message}>
              <Input disabled={isAddressSubmitting} {...registerAddress("adres")} />
            </Field>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                className="h-4 w-4 rounded-[4px] border-border"
                disabled={isAddressSubmitting}
                {...registerAddress("varsayilan")}
              />
              Varsayılan adres
            </label>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setAddressModalOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isAddressSubmitting}>
                {isAddressSubmitting ? "Kaydediliyor…" : "Kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Row({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="text-muted-foreground shrink-0">{label}</span>
      <span className="text-right text-foreground min-w-0 break-all">{value}</span>
    </div>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label>{label}</Label>
      {children}
      {error ? (
        <span className="text-[11px] text-destructive">{error}</span>
      ) : null}
    </div>
  );
}

function Info({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-[6px] border border-border px-3 py-2">
      <div className="text-[10px] text-muted-foreground">{label}</div>
      <div className={`text-xs ${mono ? "font-mono" : "font-medium"}`}>
        {value}
      </div>
    </div>
  );
}

const PasswordField = React.forwardRef<
  HTMLInputElement,
  {
    id: string;
    label: string;
    show: boolean;
    onToggle: () => void;
    error?: string;
    disabled?: boolean;
    autoComplete?: string;
  } & React.InputHTMLAttributes<HTMLInputElement>
>(function PasswordField(
  { id, label, show, onToggle, error, disabled, autoComplete, ...rest },
  ref
) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Input
          id={id}
          ref={ref}
          type={show ? "text" : "password"}
          disabled={disabled}
          autoComplete={autoComplete}
          className="pr-9"
          {...rest}
        />
        <button
          type="button"
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          onClick={onToggle}
          tabIndex={-1}
          aria-label={show ? "Gizle" : "Göster"}
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      {error ? (
        <span className="text-[11px] text-destructive">{error}</span>
      ) : null}
    </div>
  );
});
