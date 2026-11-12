export type PiyasaOlcek = "GRAM" | "ONS" | "KG" | string;

export interface PiyasaPanoSatir {
  kod: string;
  ad?: string;
  fiyat: string;
  para_birimi: string;
  olcek?: PiyasaOlcek;
  kaynak: string;
  guncelleme?: string | null;
  banner?: string | null;
}

export interface PiyasaPano {
  server_now: string;
  olcek?: string | null;
  satirlar: PiyasaPanoSatir[];
}
