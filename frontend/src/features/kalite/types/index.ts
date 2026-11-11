/**
 * OpenAPI normatif kalite kontrol tipleri (API_CONTRACT ve ADR-0021).
 */

export interface OpsInspection {
  id: number;
  order_id: number;
  durum: "BEKLEMEDE" | "INCELEMEDE" | "GECTI" | "KALDI" | "IPTAL" | string;
  allowed_actions: string[];
  server_now?: string;
  olculen_ayar?: string;
  olculen_gram?: string;
  notlar?: string;
}

export interface OpsInspectionPage {
  count: number;
  results: OpsInspection[];
}

export interface InspectionMeasurementRequest {
  olculen_ayar?: string;
  olculen_gram?: string;
  notlar?: string;
}
