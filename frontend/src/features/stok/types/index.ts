export interface StockBalance {
  id: number;
  varyant_id: number;
  depo_id: number;
  mevcut_miktar: string; // Decimal string
  rezerve_miktar: string;
  kullanilabilir_miktar: string;
}

export interface StockMovement {
  id: number;
  varyant_id: number;
  hareket_tipi: "GIRIS" | "CIKIS" | "SATIS" | "IADE" | "DUZELTME";
  miktar: string;
  tarih: string;
}
