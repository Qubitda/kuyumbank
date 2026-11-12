export interface BuyerQuoteNetOzet {
  toplam_vergisiz?: string | null;
  gram?: string | null;
  gram_basi_vergisiz?: string | null;
  iscilik_vergisiz?: string | null;
  has_gram?: string | null;
}

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
  /** GAP-F3-03 — ISCILIK satır tutarı (marj/maliyet yok) */
  iscilik_vergisiz?: string | null;
  /** GAP-F3-03 — gram × katalog milyem */
  has_gram?: string | null;
  net_ozet?: BuyerQuoteNetOzet;
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

/** OpenAPI RfqCreateRequest — line: miktar, birim?, varyant_id?, aciklama? */
export interface BuyerRfqCreateRequest {
  baslik?: string;
  talep_tipi: "STANDART" | "KATALOG_DISI" | "OZEL_URETIM" | string;
  sube_id?: number;
  lines: Array<{
    varyant_id?: number;
    miktar: string;
    birim?: string;
    aciklama?: string;
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

/** OpenAPI SupplierOfferCreateRequest */
export interface SupplierOfferCreateRequest {
  varyant_id: number;
  fiyat_modeli: string;
  birim_fiyat?: string;
  gram?: string;
  iscilik_override?: string;
  para_birimi?: string;
  tedarikci_kodu?: string;
  temin_tipi?: string;
  uretim_suresi_gun?: number;
  gecerlilik_baslangic?: string;
  gecerlilik_bitis?: string;
}
