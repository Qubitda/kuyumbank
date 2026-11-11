export interface CariHesap {
  id: number;
  firma_id: number;
  bakiye: string; // Decimal string
  para_birimi: string;
  has_bakiye?: string;
  son_hareket_tarihi?: string;
}

export interface LedgerEntry {
  id: number;
  tip: "BORC" | "ALACAK";
  tutar: string;
  para_birimi: string;
  aciklama?: string;
  tarih: string;
}

export interface CreditInfo {
  kredi_limiti: string;
  kullanilan_limit: string;
  kalan_limit: string;
  durum: string;
}
