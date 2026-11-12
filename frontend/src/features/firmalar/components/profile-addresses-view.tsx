"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { firmalarService } from "../services";
import {
  addressSchema,
  profileSchema,
  type AddressInput,
  type ProfileInput,
} from "../schemas";
import type { FirmaAdresi, MeProfile } from "../types";
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
  User,
  MapPin,
  Plus,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Building,
} from "lucide-react";

export function ProfileAddressesView() {
  const [profile, setProfile] = useState<MeProfile | null>(null);
  const [addresses, setAddresses] = useState<FirmaAdresi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [addressModalOpen, setAddressModalOpen] = useState(false);

  const {
    register: registerProfile,
    handleSubmit: handleProfileSubmit,
    reset: resetProfile,
    formState: { isSubmitting: isProfileSubmitting },
  } = useForm<ProfileInput>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
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
      il: "İstanbul",
      ilce: "Fatih",
      adres: "",
      varsayilan: true,
    },
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profileRes, addressRes] = await Promise.allSettled([
        firmalarService.getProfile(),
        firmalarService.getAddresses(),
      ]);

      if (profileRes.status === "fulfilled") {
        setProfile(profileRes.value);
        resetProfile({
          first_name: profileRes.value.first_name || "",
          last_name: profileRes.value.last_name || "",
          email: profileRes.value.email || "",
          phone: profileRes.value.phone || "",
        });
      }
      if (addressRes.status === "fulfilled") {
        setAddresses(addressRes.value?.results || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profil ve adres bilgisi alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onProfileSave = async (data: ProfileInput) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await firmalarService.updateProfile(data);
      setProfile(updated);
      setSuccessMsg("Profil bilgileri başarıyla güncellendi.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profil kaydedilemedi.");
    }
  };

  const onAddressSave = async (data: AddressInput) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await firmalarService.createAddress({
        tip: data.tip,
        il: data.il,
        ilce: data.ilce,
        adres: data.adres,
        varsayilan: data.varsayilan,
      });
      setAddressModalOpen(false);
      resetAddress();
      setSuccessMsg("Yeni adres başarıyla kaydedildi.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Adres kaydedilemedi.");
    }
  };

  const handleDeleteAddress = async (id: number) => {
    try {
      await firmalarService.deleteAddress(id);
      await fetchData();
      setSuccessMsg("Adres silindi.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Adres silinemedi.");
    }
  };

  return (
    <div className="flex flex-col gap-8 max-w-4xl">
      {/* Başlık */}
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Kullanıcı Profili & Firma Adresleri
        </h1>
        <p className="text-xs text-muted-foreground">
          Kişisel hesap ayarları, fatura ve zırhlı kargo teslimat adresleri yönetimi (ADR-0017 / F9-017).
        </p>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 rounded-[6px] border border-border bg-muted/60 p-3 text-xs text-foreground font-medium">
          <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
          <span>{successMsg}</span>
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
      ) : (
        <div className="flex flex-col gap-8">
          {/* 1. Profil Bilgileri Formu */}
          <div className="rounded-[8px] border border-border bg-card p-6 space-y-4">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <User className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">
                Kişisel Bilgiler
              </h2>
            </div>

            <form onSubmit={handleProfileSubmit(onProfileSave)} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="prof-first">Ad</Label>
                <Input
                  id="prof-first"
                  placeholder="Adınız"
                  disabled={isProfileSubmitting}
                  {...registerProfile("first_name")}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="prof-last">Soyad</Label>
                <Input
                  id="prof-last"
                  placeholder="Soyadınız"
                  disabled={isProfileSubmitting}
                  {...registerProfile("last_name")}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="prof-email">E-posta</Label>
                <Input
                  id="prof-email"
                  type="email"
                  placeholder="eposta@firma.com"
                  disabled={isProfileSubmitting}
                  {...registerProfile("email")}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="prof-phone">Telefon</Label>
                <Input
                  id="prof-phone"
                  placeholder="+90 5XX XXX XX XX"
                  disabled={isProfileSubmitting}
                  {...registerProfile("phone")}
                />
              </div>

              <div className="sm:col-span-2 flex justify-end pt-2">
                <Button type="submit" size="sm" disabled={isProfileSubmitting}>
                  {isProfileSubmitting ? "Kaydediliyor…" : "Profili Güncelle"}
                </Button>
              </div>
            </form>
          </div>

          {/* 2. Firma Adresleri Listesi ve Ekleme */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-foreground">
                  Kayıtlı Firma Adresleri (Teslimat & Fatura)
                </h2>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setAddressModalOpen(true)}
                className="h-8 text-xs gap-1.5"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Yeni Adres Ekle</span>
              </Button>
            </div>

            <div className="rounded-[8px] border border-border bg-card overflow-hidden">
              {addresses.length === 0 ? (
                <div className="p-8 text-center text-xs text-muted-foreground">
                  Tanımlı teslimat veya fatura adresi bulunmamaktadır.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[110px]">Adres Tipi</TableHead>
                      <TableHead>İl / İlçe</TableHead>
                      <TableHead>Açık Adres</TableHead>
                      <TableHead className="text-right">Varsayılan</TableHead>
                      <TableHead className="text-right">İşlem</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {addresses.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>
                          <Badge
                            variant={a.tip === "TESLIMAT" ? "default" : "secondary"}
                            className="font-mono text-[10px]"
                          >
                            {a.tip}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-medium text-foreground">
                          {a.il} {a.ilce ? `/ ${a.ilce}` : ""}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground max-w-sm truncate">
                          {a.adres}
                        </TableCell>
                        <TableCell className="text-right">
                          {a.varsayilan && (
                            <Badge variant="outline" className="font-mono text-[10px]">
                              VARSAYILAN
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteAddress(a.id)}
                            className="h-8 w-8 text-destructive hover:bg-destructive/10"
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
          </div>
        </div>
      )}

      {/* Yeni Adres Ekleme Dialog */}
      <Dialog open={addressModalOpen} onOpenChange={setAddressModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Yeni Adres Tanımı</DialogTitle>
            <DialogDescription>
              Sigortalı teslimat veya e-fatura için firma adresi ekleyin.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleAddressSubmit(onAddressSave)} className="flex flex-col gap-4 pt-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="addr-tip">Adres Türü</Label>
              <select
                id="addr-tip"
                className="h-9 w-full rounded-[6px] border border-input bg-background px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                disabled={isAddressSubmitting}
                {...registerAddress("tip")}
              >
                <option value="TESLIMAT">TESLİMAT ADRESİ (Zırhlı Kargo)</option>
                <option value="FATURA">FATURA ADRESİ (Resmi)</option>
              </select>
              {addressErrors.tip && (
                <span className="text-[11px] text-destructive">
                  {addressErrors.tip.message}
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="addr-il">İl</Label>
                <Input
                  id="addr-il"
                  placeholder="Örn: İstanbul"
                  disabled={isAddressSubmitting}
                  {...registerAddress("il")}
                />
                {addressErrors.il && (
                  <span className="text-[11px] text-destructive">
                    {addressErrors.il.message}
                  </span>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="addr-ilce">İlçe</Label>
                <Input
                  id="addr-ilce"
                  placeholder="Örn: Fatih"
                  disabled={isAddressSubmitting}
                  {...registerAddress("ilce")}
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="addr-text">Açık Adres (Cadde, Kapı No, Posta Kodu)</Label>
              <Input
                id="addr-text"
                placeholder="Kapalıçarşı Kalpakçılar Cad. No: 42"
                disabled={isAddressSubmitting}
                {...registerAddress("adres")}
              />
              {addressErrors.adres && (
                <span className="text-[11px] text-destructive">
                  {addressErrors.adres.message}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                id="addr-def"
                type="checkbox"
                className="h-4 w-4 rounded-[4px] border-border text-primary focus:ring-ring"
                disabled={isAddressSubmitting}
                {...registerAddress("varsayilan")}
              />
              <Label htmlFor="addr-def" className="text-xs cursor-pointer font-normal">
                Bu adresi varsayılan olarak belirle
              </Label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setAddressModalOpen(false)}
              >
                İptal
              </Button>
              <Button type="submit" size="sm" disabled={isAddressSubmitting}>
                {isAddressSubmitting ? "Kaydediliyor…" : "Adresi Kaydet"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
