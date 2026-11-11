"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { tanimlarService } from "../services";
import { salesChannelSchema, type SalesChannelInput } from "../schemas";
import type { SalesChannel } from "../types";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sliders, RefreshCw, AlertCircle, Coins, ShieldAlert } from "lucide-react";

export function DefinitionsView() {
  const [channels, setChannels] = useState<SalesChannel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDefinitions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await tanimlarService.getSalesChannels();
      setChannels(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tanım verileri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDefinitions();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık */}
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Tanımlar & Parametreler
        </h1>
        <p className="text-xs text-muted-foreground">
          Satış kanalları, para birimleri ve kur dayanıklılığı (ADR-0018 Cap limitleri).
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
            onClick={fetchDefinitions}
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
            <span>Parametreler alınıyor…</span>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          {/* Sistem Kur Dayanıklılığı Özeti */}
          <div className="rounded-[8px] border border-border bg-card p-5 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <ShieldAlert className="h-4 w-4 text-muted-foreground" />
              <span>Kur Güvenlik & Cap Politikası (ADR-0018)</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Döviz ve altın kurlarında ani manipülasyonları engellemek için backend motorunda
              maksimum sapma toleransı (%5 limit) ve snapshot TTL doğrulaması çalışmaktadır.
              Hesaplanan fiyatlar süresi dolduğunda otomatik olarak geçersiz kılınır.
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <Badge variant="outline" className="font-mono text-xs">
                Baz Para Birimi: TRY
              </Badge>
              <Badge variant="outline" className="font-mono text-xs">
                Has Altın Birimi: XAU / GRAM (995+ Milyem)
              </Badge>
              <Badge variant="outline" className="font-mono text-xs">
                İşlem Para Birimleri: TRY, USD, EUR
              </Badge>
            </div>
          </div>

          {/* Satış Kanalları Tablosu */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Sliders className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">
                Yetkili Satış Kanalları (Sales Channels)
              </h2>
            </div>

            <div className="rounded-[8px] border border-border bg-card overflow-hidden">
              {channels.length === 0 ? (
                <div className="p-8 text-center text-xs text-muted-foreground">
                  Tanımlı aktif satış kanalı bulunmamaktadır.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[120px]">Kanal Kodu</TableHead>
                      <TableHead>Kanal Tanımı</TableHead>
                      <TableHead>Durum</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {channels.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell className="font-mono text-xs font-semibold">
                          {c.kod}
                        </TableCell>
                        <TableCell className="font-medium text-foreground">
                          {c.ad}
                        </TableCell>
                        <TableCell>
                          <Badge variant="success" className="font-mono text-[10px]">
                            {c.aktif !== false ? "AKTİF" : "PASİF"}
                          </Badge>
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
    </div>
  );
}
