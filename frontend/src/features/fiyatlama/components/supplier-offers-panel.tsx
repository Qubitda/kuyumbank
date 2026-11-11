"use client";

import { useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createSupplierOffer,
  listSupplierOffers,
  submitSupplierOffer,
} from "@/features/fiyatlama/services";
import { ApiError } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { newIdempotencyKey } from "@/lib/utils";

type Offer = components["schemas"]["SupplierOffer"];

export function SupplierOffersPanel() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function reload() {
    return listSupplierOffers()
      .then((page) => {
        setOffers(page.results ?? []);
        setError(null);
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Teklif listesi alınamadı.",
        );
      });
  }

  useEffect(() => {
    void reload();
  }, []);

  function onCreate(formData: FormData) {
    const varyantId = Number(formData.get("varyant_id"));
    const birimFiyat = String(formData.get("birim_fiyat") || "").trim();
    const gram = String(formData.get("gram") || "").trim();
    if (!varyantId || !birimFiyat) {
      setError("varyant_id ve birim_fiyat zorunlu.");
      return;
    }
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        const body: components["schemas"]["SupplierOfferCreateRequest"] = {
          varyant_id: varyantId,
          fiyat_modeli: "GRAM",
          birim_fiyat: birimFiyat,
          para_birimi: "TRY",
        };
        if (gram) body.gram = gram;
        const created = await createSupplierOffer(body, newIdempotencyKey());
        setMessage(`Taslak teklif #${created.id}`);
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Oluşturma başarısız.");
      }
    });
  }

  function onSubmit(id: number) {
    setError(null);
    startTransition(async () => {
      try {
        await submitSupplierOffer(id, newIdempotencyKey());
        setMessage(`Teklif gönderildi #${id}`);
        await reload();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Gönderim başarısız.");
      }
    });
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Teklifler</h1>
        <p className="text-sm text-muted-foreground">
          Kısıtlı fiyat girişi — `/supplier/offers/`.
        </p>
      </header>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="text-sm text-foreground" role="status">
          {message}
        </p>
      ) : null}

      <form action={onCreate} className="grid max-w-md gap-3">
        <div className="flex flex-col gap-1">
          <Label htmlFor="varyant_id">Varyant ID</Label>
          <Input id="varyant_id" name="varyant_id" inputMode="numeric" required />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="birim_fiyat">Birim fiyat</Label>
          <Input
            id="birim_fiyat"
            name="birim_fiyat"
            className="text-right tabular-nums"
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="gram">Gram</Label>
          <Input
            id="gram"
            name="gram"
            className="text-right tabular-nums"
          />
        </div>
        <Button type="submit" disabled={pending}>
          Taslak oluştur
        </Button>
      </form>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-2 pr-3 font-medium">ID</th>
              <th className="py-2 pr-3 font-medium">Varyant</th>
              <th className="py-2 pr-3 text-right font-medium tabular-nums">
                Fiyat
              </th>
              <th className="py-2 pr-3 text-right font-medium tabular-nums">
                Gram
              </th>
              <th className="py-2 pr-3 font-medium">Durum</th>
              <th className="py-2 font-medium"> </th>
            </tr>
          </thead>
          <tbody>
            {offers.map((o) => (
              <tr key={o.id} className="border-b border-border">
                <td className="py-2 pr-3 font-mono text-xs">#{o.id}</td>
                <td className="py-2 pr-3 tabular-nums">{o.varyant_id}</td>
                <td className="py-2 pr-3 text-right tabular-nums">
                  {o.birim_fiyat} {o.para_birimi}
                </td>
                <td className="py-2 pr-3 text-right tabular-nums">
                  {o.gram ?? "—"}
                </td>
                <td className="py-2 pr-3">{o.durum}</td>
                <td className="py-2">
                  {o.allowed_actions?.includes("submit") ? (
                    <Button
                      type="button"
                      size="sm"
                      disabled={pending}
                      onClick={() => onSubmit(o.id)}
                    >
                      Gönder
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
