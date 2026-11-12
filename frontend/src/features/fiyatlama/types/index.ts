export interface PriceQuote {
  id: number;
  varyant_id: number;
  /** Gösterim: gram_basi veya toplam (OpenAPI BuyerQuote) */
  birim_fiyat: string;
  para_birimi: string;
  expires_at?: string;
  allowed_actions?: string[];
  durum?: string;
  gram?: string;
  gram_basi_vergisiz?: string;
  toplam_vergisiz?: string;
  varyant_sku?: string;
  urun?: string;
}

export interface PriceLock {
  id: number;
  quote_id: number;
  kilit_fiyati: string;
  para_birimi: string;
  durum: "AKTIF" | "KULLANILDI" | "SURESI_DOLDU" | "IPTAL" | string;
  expires_at: string;
  gecerli?: boolean;
}

export interface SupplierRfqLine {
  id?: number;
  varyant_id?: number;
  miktar?: string;
  birim?: string;
  notlar?: string;
  hedef_gram?: string;
  hedef_ayar?: string;
  aciklama?: string;
}

export interface SupplierRfq {
  id: number;
  baslik?: string;
  talep_tipi: string;
  durum: "TASLAK" | "GONDERILDI" | "TEKLIF_ALINDI" | "KAPANDI" | "IPTAL" | string;
  allowed_actions: string[];
  server_now?: string;
  lines?: SupplierRfqLine[];
  messages?: any[];
  revizyonlar?: any[];
}

export interface SupplierRfqPage {
  count: number;
  results: SupplierRfq[];
}

export interface BuyerRfqCreateRequest {
  baslik?: string;
  talep_tipi: "STANDART" | "KATALOG_DISI" | "OZEL_URETIM";
  sube_id?: number;
  lines: Array<{
    varyant_id?: number;
    miktar: string;
    hedef_gram?: string;
    hedef_ayar?: string;
    aciklama?: string;
    notlar?: string;
  }>;
}

export interface SupplierOffer {
  id: number;
  varyant_id: number;
  birim_fiyat: string | null;
  para_birimi: string;
  durum: "TASLAK" | "GONDERILDI" | "ONAYLANDI" | "PASIF" | string;
  allowed_actions: string[];
  tedarikci_kodu?: string;
  versiyon?: number;
  gecerlilik_bitis?: string | null;
}

export interface SupplierOfferPage {
  count: number;
  results: SupplierOffer[];
}

export interface SupplierOfferCreateRequest {
  rfq_id?: number;
  varyant_id: number;
  birim_fiyat: string;
  para_birimi?: string;
  teslim_gunu?: number;
}
