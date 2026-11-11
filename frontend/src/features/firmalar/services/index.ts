import { apiFetch } from "@/lib/api/client";
import type { OrgUnitPage, OrgUnit, OrgUnitCreateRequest, ApprovalPage, Approval } from "../types";

export const firmalarService = {
  getOrgUnits(): Promise<OrgUnitPage> {
    return apiFetch<OrgUnitPage>("/org-units/");
  },
  createOrgUnit(data: OrgUnitCreateRequest): Promise<OrgUnit> {
    return apiFetch<OrgUnit>("/org-units/", {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  getApprovals(): Promise<ApprovalPage> {
    return apiFetch<ApprovalPage>("/approvals/");
  },
  approveApproval(id: number | string): Promise<Approval> {
    return apiFetch<Approval>(`/approvals/${id}/approve/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  rejectApproval(id: number | string): Promise<Approval> {
    return apiFetch<Approval>(`/approvals/${id}/reject/`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
};
