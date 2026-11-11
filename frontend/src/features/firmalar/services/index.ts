import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type OrgPage = components["schemas"]["OrgUnitPage"];
type OrgUnit = components["schemas"]["OrgUnit"];
type ApprovalPage = components["schemas"]["ApprovalPage"];
type Approval = components["schemas"]["Approval"];

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
