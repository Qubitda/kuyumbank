/**
 * OpenAPI normatif firmalar ve organizasyon birimleri tipleri.
 */

export interface OrgUnit {
  id: number;
  kod: string;
  ad: string;
  parent_id?: number | null;
  server_now?: string;
  allowed_actions?: string[];
}

export interface OrgUnitPage {
  count: number;
  results: OrgUnit[];
}

export interface Approval {
  id: number;
  tutar: string;
  para_birimi?: string;
  durum: "BEKLEMEDE" | "ONAYLANDI" | "REDDEDILDI" | string;
  order_id?: number | null;
  gerekce?: string;
  allowed_actions: string[];
  server_now?: string;
}

export interface ApprovalPage {
  count: number;
  results: Approval[];
}

export interface OrgUnitCreateRequest {
  kod: string;
  ad: string;
  parent_id?: number | null;
}
