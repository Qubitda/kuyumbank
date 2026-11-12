/**
 * OpenAPI'de /belgeler/ yok. Belge benzeri kayıtlar sevkiyat / sipariş / ledger referanslarından türetilir.
 */
export type DocumentSource =
  | "shipment"
  | "ops_shipment"
  | "order"
  | "ledger";

export interface DocumentItem {
  id: string;
  belge_tipi: string;
  ad: string;
  /** http(s) ise indirilebilir; aksi metin referans */
  dosya_url?: string;
  referans_tipi: DocumentSource;
  referans_id: number;
  olusturma_tarihi?: string;
  raw_ref?: string;
}
