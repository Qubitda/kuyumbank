/**
 * OpenAPI normatif firmalar, profil, üyeler ve organizasyon birimleri tipleri.
 */

export interface MeProfile {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
}

export interface FirmaAdresi {
  id: number;
  firma_id: number;
  tip: "TESLIMAT" | "FATURA" | string;
  baslik?: string;
  il: string;
  ilce?: string;
  adres: string;
  varsayilan: boolean;
  olusturma_tarihi?: string;
}

export interface FirmaAdresiPage {
  count: number;
  results: FirmaAdresi[];
}

export interface FirmaAdresiCreateRequest {
  tip: "TESLIMAT" | "FATURA";
  il: string;
  ilce?: string;
  adres: string;
  varsayilan?: boolean;
}

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

export interface OrgMember {
  id: number;
  user_id: number;
  username?: string;
  email?: string;
  rol?: string;
  sube_id?: number;
  olusturma_tarihi?: string;
}

export interface OrgMemberPage {
  count: number;
  results: OrgMember[];
}

export interface InviteItem {
  id: number;
  email: string;
  rol: string;
  durum: "BEKLEMEDE" | "KABUL_EDILDI" | "IPTAL" | string;
  expires_at?: string;
  olusturma_tarihi?: string;
}

export interface InvitePage {
  count: number;
  results: InviteItem[];
}

export interface InviteCreateRequest {
  email: string;
  rol: string;
  sube_id?: number;
}
