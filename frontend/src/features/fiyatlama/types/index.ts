export interface PriceQuote {
  id: number;
  varyant_id: number;
  birim_fiyat: string; // Decimal string
  para_birimi: string;
  has_maliyeti?: string;
  iscilik?: string;
  ttl_saniye?: number;
  expires_at?: string;
  price_lock_id?: number | null;
}

export interface PriceLock {
  id: number;
  quote_id: number;
  kilit_fiyati: string; // Decimal string
  para_birimi: string;
  durum: "AKTIF" | "KULLANILDI" | "SURESI_DOLDU" | "IPTAL";
  expires_at: string;
}
