/** OpenAPI MeProfile + adres / güvenlik yanıtları */

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

export interface ProfilePatchRequest {
  first_name?: string;
  last_name?: string;
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
  results: FirmaAdresi[];
  next?: string | null;
  previous?: string | null;
}

export interface FirmaAdresiCreateRequest {
  tip: "TESLIMAT" | "FATURA" | string;
  il: string;
  ilce?: string;
  adres: string;
  varsayilan?: boolean;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

export interface DetailOk {
  detail: string;
}
