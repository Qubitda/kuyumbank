/**
 * OpenAPI’de `/belgeler/` yok.
 * Belge satırları sevkiyat (POD belgeler_ref), sipariş, ledger ve iade uçlarından türetilir.
 */

export type DocumentSource =
  | "shipment"
  | "ops_shipment"
  | "order"
  | "ledger"
  | "return"
  | "inspection";

export type DocumentCategory =
  | "SEVKIYAT"
  | "POD"
  | "SIPARIS"
  | "LEDGER"
  | "IADE"
  | "KALITE"
  | "DIGER";

export interface DocumentItem {
  id: string;
  belge_tipi: DocumentCategory | string;
  ad: string;
  belge_no?: string;
  durum?: string;
  /** http(s) ise önizleme/indirme; aksi harici storage anahtarı */
  dosya_url?: string;
  raw_ref?: string;
  referans_tipi: DocumentSource;
  referans_id: number;
  related_order_id?: number | null;
  olusturma_tarihi?: string;
  format?: string;
  meta?: Record<string, string | number | boolean | null | undefined>;
  allowed_actions?: string[];
  href?: string;
}

export interface PodAttachRequest {
  shipment_id: number;
  teslim_alan: string;
  notlar?: string;
  belgeler_ref?: string;
}

export interface DocumentsSnapshot {
  items: DocumentItem[];
  errors: Partial<Record<DocumentSource, string>>;
}
