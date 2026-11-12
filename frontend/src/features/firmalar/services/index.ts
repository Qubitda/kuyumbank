import { apiFetch } from "@/lib/api/client";
import type {
  OrgUnitPage,
  OrgUnit,
  OrgUnitCreateRequest,
  ApprovalPage,
  Approval,
  MeProfile,
  FirmaAdresiPage,
  FirmaAdresi,
  FirmaAdresiCreateRequest,
  OrgMemberPage,
  OrgMember,
  InvitePage,
  InviteItem,
  InviteCreateRequest,
} from "../types";

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
  getProfile(): Promise<MeProfile> {
    return apiFetch<MeProfile>("/me/profile/");
  },
  updateProfile(data: Partial<MeProfile>): Promise<MeProfile> {
    return apiFetch<MeProfile>("/me/profile/", {
      method: "PATCH",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  getAddresses(): Promise<FirmaAdresiPage> {
    return apiFetch<FirmaAdresiPage>("/me/addresses/");
  },
  createAddress(data: FirmaAdresiCreateRequest): Promise<FirmaAdresi> {
    return apiFetch<FirmaAdresi>("/me/addresses/", {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  deleteAddress(id: number | string): Promise<void> {
    return apiFetch<void>(`/me/addresses/${id}/`, {
      method: "DELETE",
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  getOrgMembers(orgId: number | string): Promise<OrgMemberPage> {
    return apiFetch<OrgMemberPage>(`/org-units/${orgId}/members/`);
  },
  addOrgMember(orgId: number | string, data: { user_id: number; rol: string }): Promise<OrgMember> {
    return apiFetch<OrgMember>(`/org-units/${orgId}/members/`, {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
  getInvites(): Promise<InvitePage> {
    return apiFetch<InvitePage>("/auth/invites/");
  },
  createInvite(data: InviteCreateRequest): Promise<InviteItem> {
    return apiFetch<InviteItem>("/auth/invites/create/", {
      method: "POST",
      body: data,
      idempotencyKey: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    });
  },
};
