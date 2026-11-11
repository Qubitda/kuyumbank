import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type OrgPage = components["schemas"]["OrgUnitPage"];
type OrgUnit = components["schemas"]["OrgUnit"];
type ApprovalPage = components["schemas"]["ApprovalPage"];
type Approval = components["schemas"]["Approval"];
type MeProfile = components["schemas"]["MeProfile"];
type FirmaAdresi = components["schemas"]["FirmaAdresi"];
type FirmaAdresiPage = components["schemas"]["FirmaAdresiPage"];
type DetailOk = components["schemas"]["DetailOk"];

export function listOrgUnits(): Promise<OrgPage> {
  return apiFetch<OrgPage>("/org-units/");
}

export function createOrgUnit(
  body: components["schemas"]["OrgUnitCreateRequest"],
  idempotencyKey: string,
): Promise<OrgUnit> {
  return apiFetch<OrgUnit>("/org-units/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}

export function listApprovals(): Promise<ApprovalPage> {
  return apiFetch<ApprovalPage>("/approvals/");
}

export function createApproval(
  body: components["schemas"]["ApprovalCreateRequest"],
  idempotencyKey: string,
): Promise<Approval> {
  return apiFetch<Approval>("/approvals/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}

/** F9-017 — GET /me/profile/ */
export function getMyProfile(): Promise<MeProfile> {
  return apiFetch<MeProfile>("/me/profile/");
}

/** F9-017 — PATCH /me/profile/ (first_name/last_name) */
export function updateMyProfile(
  body: components["schemas"]["ProfilePatchRequest"],
): Promise<MeProfile> {
  return apiFetch<MeProfile>("/me/profile/", {
    method: "PATCH",
    body,
  });
}

/** F9-017 — GET /me/addresses/ */
export function listMyAddresses(query?: {
  tip?: string;
  page?: number;
  page_size?: number;
}): Promise<FirmaAdresiPage> {
  const params = new URLSearchParams();
  if (query?.tip) params.set("tip", query.tip);
  if (query?.page != null) params.set("page", String(query.page));
  if (query?.page_size != null) params.set("page_size", String(query.page_size));
  const suffix = params.toString() ? `?${params}` : "";
  return apiFetch<FirmaAdresiPage>(`/me/addresses/${suffix}`);
}

/** F9-017 — POST /me/addresses/ */
export function createMyAddress(
  body: components["schemas"]["AddressCreateRequest"],
  idempotencyKey: string,
): Promise<FirmaAdresi> {
  return apiFetch<FirmaAdresi>("/me/addresses/", {
    method: "POST",
    body,
    idempotencyKey,
  });
}

/** F9-017 — GET /me/addresses/{id}/ */
export function getMyAddress(id: number): Promise<FirmaAdresi> {
  return apiFetch<FirmaAdresi>(`/me/addresses/${id}/`);
}

/** F9-017 — PATCH /me/addresses/{id}/ */
export function updateMyAddress(
  id: number,
  body: components["schemas"]["AddressPatchRequest"],
  idempotencyKey: string,
): Promise<FirmaAdresi> {
  return apiFetch<FirmaAdresi>(`/me/addresses/${id}/`, {
    method: "PATCH",
    body,
    idempotencyKey,
  });
}

/** F9-017 — DELETE /me/addresses/{id}/ */
export function deleteMyAddress(
  id: number,
  idempotencyKey: string,
): Promise<DetailOk> {
  return apiFetch<DetailOk>(`/me/addresses/${id}/`, {
    method: "DELETE",
    idempotencyKey,
  });
}
