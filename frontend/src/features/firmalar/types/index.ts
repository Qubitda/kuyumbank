/**
 * OpenAPI normatif firmalar / org / approval / invite tipleri.
 * Tenant dışı firma listesi HTTP ucu yoktur; görünür firma /me/ üzerinden gelir.
 */

export interface FirmaMasked {
  id: number;
  ad: string;
  alici_mi: boolean;
  tedarikci_mi: boolean;
  platform_mu: boolean;
  aktif: boolean;
}

export interface MeProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  rol: string;
  email_verified: boolean;
  firma?: FirmaMasked | null;
  allowed_actions?: string[];
  server_now?: string;
}

export interface FirmaAdresi {
  id: number;
  firma_id: number;
  tip: string;
  il: string;
  ilce?: string;
  adres: string;
  varsayilan: boolean;
  allowed_actions?: string[];
  server_now?: string;
}

export interface FirmaAdresiPage {
  count: number;
  page?: number;
  page_size?: number;
  next?: string | null;
  previous?: string | null;
  results: FirmaAdresi[];
}

export interface FirmaAdresiCreateRequest {
  tip: "TESLIMAT" | "FATURA" | string;
  il: string;
  ilce?: string;
  adres: string;
  varsayilan?: boolean;
}

export interface OrgUnit {
  id: number;
  kod: string;
  ad: string;
  firma_id?: number;
  parent_id?: number | null;
  aktif?: boolean;
  server_now?: string;
  allowed_actions?: string[];
}

export interface OrgUnitPage {
  count: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: OrgUnit[];
}

export interface OrgUnitCreateRequest {
  kod: string;
  ad?: string;
  parent_id?: number | null;
}

export interface Approval {
  id: number;
  tutar: string;
  para_birimi?: string;
  durum: string;
  order_id?: number | null;
  org_birimi_id?: number | null;
  gerekce?: string;
  olusturma_tarihi?: string | null;
  allowed_actions: string[];
  server_now?: string;
}

export interface ApprovalPage {
  count: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: Approval[];
}

export interface ApprovalCreateRequest {
  tutar: string;
  para_birimi?: string;
  order_id?: number;
  org_birimi_id?: number;
  gerekce?: string;
}

export interface OrgMember {
  id: number;
  org_birimi_id: number;
  kullanici_id: number;
  olusturma_tarihi?: string | null;
  allowed_actions?: string[];
  server_now?: string;
}

export interface OrgMemberPage {
  count: number;
  page?: number;
  page_size?: number;
  next?: string | null;
  previous?: string | null;
  results: OrgMember[];
}

export interface OrgMemberCreateRequest {
  kullanici_id: number;
}

export interface InviteItem {
  id: number;
  email: string;
  rol: string;
  firma_id?: number;
  expires_at?: string;
  expired?: boolean;
  durum?: string;
  olusturma_tarihi?: string;
}

export interface InvitePage {
  results: InviteItem[];
  count?: number;
}

export interface InviteCreateRequest {
  email: string;
  rol: string;
  firma_id?: number;
}
