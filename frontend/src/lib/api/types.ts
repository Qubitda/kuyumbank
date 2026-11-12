/**
 * API tipleri — OpenAPI’den üretilen `schema.d.ts` kaynağıdır.
 * Güncelleme: `npm run generate:api`
 * Decimal/para/gram string; float yok.
 */

import type { components } from "./schema";

export type { components, paths, operations } from "./schema";

type S = components["schemas"];

export type ProblemDetail = S["ProblemDetail"];
export type Capabilities = S["Capabilities"];
export type FirmaMasked = S["FirmaMasked"];
export type MeResponse = S["MeResponse"] & {
  /** Login yanıtında olabilir */
  mfa_required?: boolean;
  mfa_ok?: boolean;
};
export type LoginResponse = MeResponse;
export type MeDashboard = S["MeDashboard"];
export type CsrfResponse = S["CsrfResponse"];
export type CheckoutResult = S["CheckoutResult"];
export type BuyerFinanceSummary = S["BuyerFinanceSummary"];
export type BuyerCari = S["BuyerCari"];
export type BuyerCredit = S["BuyerCredit"];
export type BuyerLedger = S["BuyerLedger"];
export type BuyerQuote = S["BuyerQuote"];
export type PiyasaPano = S["PiyasaPano"];
export type PiyasaPanoSatir = S["PiyasaPanoSatir"];
export type BuyerPriceLock = S["BuyerPriceLock"];
export type SupplierStock = S["SupplierStock"];
export type BuyerShipment = S["BuyerShipment"];
export type BuyerCart = S["BuyerCart"];

export interface Paginated<T> {
  count: number;
  page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface HealthResponse {
  status: string;
  api?: string;
  service?: string;
}

export type ReadyResponse = S["Ready"] & {
  status: "ready" | "not_ready" | string;
};
