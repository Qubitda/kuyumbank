/**
 * OpenAPI normatif lojistik ve sevkiyat tipleri (API_CONTRACT ve ADR-0021).
 */

export interface OpsShipment {
  id: number;
  order_id: number;
  durum: "HAZIRLANIYOR" | "SEVK_EDILDI" | "TESLIM_EDILDI" | "IPTAL" | string;
  allowed_actions: string[];
  server_now?: string;
  tasiyici?: string;
  takip_no?: string;
}

export interface OpsShipmentPage {
  count: number;
  results: OpsShipment[];
}

export interface BuyerReturn {
  id: number;
  order_id: number;
  durum: "BEKLEMEDE" | "ONAYLANDI" | "REDDEDILDI" | "MAHSUP_EDILDI" | string;
  allowed_actions: string[];
  sebep?: string;
  mahsup_tutari?: string;
}

export interface BuyerReturnPage {
  count: number;
  results: BuyerReturn[];
}

export interface DispatchShipmentRequest {
  tasiyici: string;
  takip_no: string;
}
