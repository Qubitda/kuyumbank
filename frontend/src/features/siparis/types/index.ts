/**
 * OpenAPI normatif sepet ve sipariş tipleri (API_CONTRACT ve ADR-0011/0017).
 * Fiyat ve miktar hesaplamaları daima backend otoritesindedir.
 */

export interface BuyerCartLine {
  id: number;
  varyant_id: number;
  quote_id: number;
  miktar: string; // Decimal string
  birim: string;
  birim_fiyat_vergisiz: string;
  para_birimi: string;
  gecerlilik_sonu: string | null;
}

export interface BuyerCart {
  id: number;
  alici_firma_id: number;
  sube_id: number | null;
  line_count: number;
  server_now: string;
  allowed_actions: string[];
  lines: BuyerCartLine[];
}

export interface BuyerOrderLine {
  id: number;
  varyant_id: number;
  miktar: string;
  birim: string;
  snapshot_birim_fiyat_vergisiz: string;
  snapshot_satir_tutari_vergisiz: string;
  para_birimi: string;
}

export interface BuyerOrder {
  id: number;
  alici_firma_id: number;
  durum: "TASLAK" | "BEKLEMEDE" | "ONAYLANDI" | "HAZIRLANIYOR" | "SEVKIYAT" | "TAMAMLANDI" | "IPTAL" | string;
  idempotency_key: string | null;
  line_count: number;
  olusturma_tarihi: string;
  allowed_actions: string[];
  lines?: BuyerOrderLine[];
}

export interface CheckoutRequest {
  teslimat_adresi_id?: number;
  fatura_adresi_id?: number;
  notlar?: string;
}
