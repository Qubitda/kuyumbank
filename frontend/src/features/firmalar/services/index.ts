import { apiFetch, newIdempotencyKey } from "@/lib/api/client";
import type { MeDashboard, MeResponse } from "@/lib/api/types";
import type {
  OrgUnitPage,
  OrgUnit,
  OrgUnitCreateRequest,
  ApprovalPage,
  Approval,
  ApprovalCreateRequest,
  MeProfile,
  FirmaAdresiPage,
  FirmaAdresi,
  FirmaAdresiCreateRequest,
  OrgMemberPage,
  OrgMember,
  OrgMemberCreateRequest,
  InvitePage,
  InviteItem,
  InviteCreateRequest,
} from "../types";

export const firmalarService = {
  getMe(): Promise<MeResponse> {
    return apiFetch<MeResponse>("/me/");
  },
  getMeDashboard(): Promise<MeDashboard> {
    return apiFetch<MeDashboard>("/me/dashboard/");
  },
  getOrgUnits(params?: Record<string, string>): Promise<OrgUnitPage> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch<OrgUnitPage>(`/org-units/${query}`);
  },
  getOrgUnit(id: number | string): Promise<OrgUnit> {
    return apiFetch<OrgUnit>(`/org-units/${id}/`);
  },
  createOrgUnit(data: OrgUnitCreateRequest): Promise<OrgUnit> {
    return apiFetch<OrgUnit>("/org-units/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  getApprovals(params?: Record<string, string>): Promise<ApprovalPage> {
    const query = params ? `?${new URLSearchParams(params).toString()}` : "";
    return apiFetch<ApprovalPage>(`/approvals/${query}`);
  },
  createApproval(data: ApprovalCreateRequest): Promise<Approval> {
    return apiFetch<Approval>("/approvals/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  getApproval(id: number | string): Promise<Approval> {
    return apiFetch<Approval>(`/approvals/${id}/`);
  },
  submitApproval(id: number | string): Promise<Approval> {
    return apiFetch<Approval>(`/approvals/${id}/submit/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  approveApproval(id: number | string): Promise<Approval> {
    return apiFetch<Approval>(`/approvals/${id}/approve/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  rejectApproval(id: number | string): Promise<Approval> {
    return apiFetch<Approval>(`/approvals/${id}/reject/`, {
      method: "POST",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  getProfile(): Promise<MeProfile> {
    return apiFetch<MeProfile>("/me/profile/");
  },
  updateProfile(data: { first_name?: string; last_name?: string }): Promise<MeProfile> {
    return apiFetch<MeProfile>("/me/profile/", {
      method: "PATCH",
      body: data,
    });
  },
  getAddresses(): Promise<FirmaAdresiPage> {
    return apiFetch<FirmaAdresiPage>("/me/addresses/");
  },
  createAddress(data: FirmaAdresiCreateRequest): Promise<FirmaAdresi> {
    return apiFetch<FirmaAdresi>("/me/addresses/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  updateAddress(
    id: number | string,
    data: Partial<FirmaAdresiCreateRequest>
  ): Promise<FirmaAdresi> {
    return apiFetch<FirmaAdresi>(`/me/addresses/${id}/`, {
      method: "PATCH",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  deleteAddress(id: number | string): Promise<void> {
    return apiFetch<void>(`/me/addresses/${id}/`, {
      method: "DELETE",
      idempotencyKey: newIdempotencyKey(),
    });
  },
  getOrgMembers(orgId: number | string): Promise<OrgMemberPage> {
    return apiFetch<OrgMemberPage>(`/org-units/${orgId}/members/`);
  },
  addOrgMember(
    orgId: number | string,
    data: OrgMemberCreateRequest
  ): Promise<OrgMember> {
    return apiFetch<OrgMember>(`/org-units/${orgId}/members/`, {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
  getInvites(): Promise<InvitePage> {
    return apiFetch<InvitePage>("/auth/invites/");
  },
  createInvite(data: InviteCreateRequest): Promise<InviteItem> {
    return apiFetch<InviteItem>("/auth/invites/create/", {
      method: "POST",
      body: data,
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
