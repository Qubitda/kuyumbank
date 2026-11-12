/**
 * OpenAPI / presenter tipleri (API_CONTRACT). Alan uydurma yok.
 * Decimal/para/gram string olarak işlenir.
 */

export interface ProblemDetail {
  type?: string;
  title?: string;
  status: number;
  detail?: string;
  code?: string;
  request_id?: string;
  errors?: Record<string, string[] | string>;
}

export interface Paginated<T> {
  count: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FirmaMasked {
  id: number;
  ad: string;
  alici_mi: boolean;
  tedarikci_mi: boolean;
  platform_mu: boolean;
  aktif: boolean;
}

export interface Capabilities {
  can_checkout: boolean;
  can_view_catalog: boolean;
  can_view_cart: boolean;
  can_view_orders: boolean;
  can_view_finance: boolean;
  can_view_credit: boolean;
  can_view_shipments: boolean;
  can_approve: boolean;
  can_manage_rfq: boolean;
  can_manage_org: boolean;
  can_lock_quote: boolean;
  can_manage_offers: boolean;
  can_view_supplier_stock: boolean;
  can_view_ops: boolean;
  can_view_ops_finance: boolean;
  can_manage_qc: boolean;
  can_manage_shipment: boolean;
  can_manage_return: boolean;
}

export interface MeResponse {
  id: number;
  username: string;
  rol: string;
  firma: FirmaMasked | null;
  firma_id: number | null;
  capabilities: Capabilities;
}

export interface MeDashboard {
  cart_id?: number;
  cart_line_count?: number;
  firma_ad?: string;
  firma_id?: number | null;
  firma_kodu?: string;
  order_count?: number;
  rfq_count?: number;
  rfq_ozel_count?: number;
  rol?: string;
  username?: string;
}

export interface HealthResponse {
  status: string;
  api?: string;
  service?: string;
}

export interface ReadyResponse {
  status: "ready" | "not_ready" | string;
  service?: string;
  api?: string;
  checks: { database: string; [key: string]: string };
}

export interface CsrfResponse {
  csrf_token: string;
}

export interface BuyerFinanceSummary {
  para_birimi?: string;
  server_now: string;
  allowed_actions?: string[];
}

export interface BuyerCari {
  id: number;
  para_birimi: string;
  bakiye: string;
  kredi_limiti?: string;
  guncelleme_tarihi?: string | null;
  allowed_actions?: string[];
  server_now?: string;
}

export interface BuyerCredit {
  para_birimi: string;
  bakiye: string;
  kredi_limiti: string;
  kullanilabilir?: string | null;
  limit_aktif: boolean;
}

export interface BuyerLedger {
  id: number;
  tutar: string;
  para_birimi: string;
  yon?: string;
  hareket_tipi?: string;
  referans_tip?: string;
  referans_id?: number | null;
  olusturma_tarihi?: string | null;
  allowed_actions?: string[];
  server_now?: string;
}

export interface CheckoutResult {
  checkout_id: number;
  durum?: string;
  order_id?: number | null;
  server_now?: string;
}

export interface BuyerQuote {
  id: number;
  toplam_vergisiz: string;
  para_birimi: string;
  server_now: string;
  varyant_id?: number;
  varyant_sku?: string;
  urun?: string;
  gram?: string;
  gram_basi_vergisiz?: string;
  durum?: string;
  expires_at?: string | null;
  hesap_zamani?: string | null;
  satis_kanali_kod?: string;
  belge_turu?: string;
  satirlar?: unknown[] | null;
  allowed_actions?: string[];
}

export interface BuyerPriceLock {
  id: number;
  quote_id: number;
  toplam_vergisiz?: string;
  para_birimi?: string;
  durum?: string;
  gecerli?: boolean;
  expires_at?: string | null;
  kilit_zamani?: string | null;
  server_now?: string;
  allowed_actions?: string[];
}

export interface SupplierStock {
  varyant_id: number;
  birim: string;
  available: string;
  on_hand?: string;
  reserved?: string;
  blocked?: string;
  teklif_id?: number;
  warehouse_id?: number;
}

export interface BuyerShipment {
  id: number;
  durum: string;
  order_id?: number;
  server_now?: string;
  allowed_actions?: string[];
}
