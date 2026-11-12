/** OpenAPI TicariSiparisOzet */
export interface CommercialOrderReport {
  scope: string;
  siparis_adet: number;
  ciro_vergisiz: string;
  read_model: string;
  alici_firma_id?: number | null;
  satir_adet?: number;
  siparis_iptal?: number;
  siparis_olusturuldu?: number;
}

/** OpenAPI AliciDavranisOzet */
export interface BuyerBehaviorReport {
  scope: string;
  alici_firma_id: number;
  read_model: string;
  siparis_adet?: number;
  satir_adet?: number;
  ciro_vergisiz?: string;
  quote_adet?: number;
  quote_toplam_sum?: string;
}

/** OpenAPI CiroAnomali */
export interface AnomalyOrderResult {
  id?: number;
  alici_firma_id?: number;
  ciro?: string;
  olusturma_tarihi?: string;
  durum?: string;
  [key: string]: unknown;
}

export interface RevenueAnomalyReport {
  scope: string;
  esik_ciro: string;
  uyari_adet: number;
  uyarilar: AnomalyOrderResult[];
  read_model: string;
}
