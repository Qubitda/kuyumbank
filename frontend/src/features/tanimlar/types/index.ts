export interface SalesChannel {
  id: number;
  kod: string;
  ad: string;
  aktif?: boolean;
}

export interface KurBilgisi {
  para_birimi: string;
  oran: string;
  tarih?: string;
}
