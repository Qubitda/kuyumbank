"use client";

import React, { useState, useEffect } from "react";
import { belgelerService } from "../services";
import type { DocumentItem } from "../types";
import { formatDateTime } from "@/lib/format";
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
import { FileText, Download, RefreshCw, AlertCircle, ShieldCheck } from "lucide-react";

export function DocumentsView() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await belgelerService.getDocuments();
      setDocuments(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Belge listesi alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* Başlık */}
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Belgeler & Değerli Taş Sertifikaları
        </h1>
        <p className="text-xs text-muted-foreground">
          GIA/HRD pırlanta analiz raporları, sevk irsaliyeleri ve dijital onay evrakları.
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
            onClick={fetchDocuments}
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
            <span>Belgeler yükleniyor…</span>
          </div>
        </div>
      ) : (
        <div className="rounded-[8px] border border-border bg-card overflow-hidden">
          {documents.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center gap-2 text-center p-6 text-xs text-muted-foreground">
              <ShieldCheck className="h-8 w-8 opacity-40 mb-1" />
              <span className="text-sm font-medium text-foreground">Sertifika ve evrak arşivi hazır</span>
              <span className="max-w-sm">
                Sipariş edilen mücevher ve değerli taşlara ait resmi laboratuvar sertifikaları burada saklanır.
              </span>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[120px]">Belge Türü</TableHead>
                  <TableHead>Belge Adı</TableHead>
                  <TableHead>İlişkili Referans</TableHead>
                  <TableHead>Kayıt Tarihi</TableHead>
                  <TableHead className="text-right">İşlem</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px]">
                        {d.belge_tipi}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-medium text-foreground">
                      {d.ad}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {d.referans_tipi} #{d.referans_id}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDateTime(d.olusturma_tarihi)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" className="h-8 text-xs gap-1.5">
                        <Download className="h-3.5 w-3.5" />
                        <span>İndir</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      )}
    </div>
  );
}
