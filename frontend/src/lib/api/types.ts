/** Doğrulanmış OpenAPI / presenter şekilleri — alan uydurma yok (API_CONTRACT). */

export type ProblemDetail = {
  type?: string;
  title?: string;
  status: number;
  detail?: string;
  code?: string;
  request_id?: string;
};

export type FirmaMasked = {
  id: number;
  ad: string;
  alici_mi: boolean;
  tedarikci_mi: boolean;
  platform_mu: boolean;
  aktif: boolean;
};

export type Capabilities = {
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
};

export type MeResponse = {
  id: number;
  username: string;
  rol: string;
  firma: FirmaMasked | null;
  firma_id: number | null;
  capabilities: Capabilities;
};

export type HealthResponse = {
  status: string;
  api?: string;
};

export type CsrfResponse = {
  csrf_token: string;
};
