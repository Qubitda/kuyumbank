export interface FinanceSummary {
  para_birimi?: string;
  server_now: string;
  allowed_actions?: string[];
}

export interface CariHesap {
  id: number;
  para_birimi: string;
  bakiye: string;
  kredi_limiti?: string;
  guncelleme_tarihi?: string | null;
  allowed_actions?: string[];
  server_now?: string;
}

export interface LedgerEntry {
  id: number;
  tutar: string;
  para_birimi: string;
  yon?: string;
  hareket_tipi?: string;
  referans_tip?: string;
  referans_id?: number | null;
  olusturma_tarihi?: string | null;
}

export interface CreditInfo {
  para_birimi: string;
  bakiye: string;
  kredi_limiti: string;
  kullanilabilir?: string | null;
  limit_aktif: boolean;
}

export interface PaymentIntent {
  id: number;
  tutar?: string;
  para_birimi?: string;
  durum?: string;
  client_secret?: string;
}
