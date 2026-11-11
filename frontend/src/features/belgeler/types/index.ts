export interface DocumentItem {
  id: number;
  belge_tipi: "TAS_SERTIFIKASI" | "SEVKIYAT_IRSALIYESI" | "FATURA" | "SOZLESME";
  ad: string;
  dosya_url?: string;
  referans_tipi?: string;
  referans_id?: number;
  olusturma_tarihi: string;
}
