"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { firmalarService } from "../services";
import type {
  ApprovalCreateRequest,
  FirmaAdresiCreateRequest,
  InviteCreateRequest,
  OrgMemberCreateRequest,
  OrgUnitCreateRequest,
} from "../types";

export const firmalarKeys = {
  all: ["firmalar"] as const,
  me: () => [...firmalarKeys.all, "me"] as const,
  dashboard: () => [...firmalarKeys.all, "dashboard"] as const,
  units: () => [...firmalarKeys.all, "units"] as const,
  unitMembers: (id: number | string) =>
    [...firmalarKeys.all, "unit-members", String(id)] as const,
  approvals: () => [...firmalarKeys.all, "approvals"] as const,
  invites: () => [...firmalarKeys.all, "invites"] as const,
  addresses: () => [...firmalarKeys.all, "addresses"] as const,
};

function invalidateFirmalar(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: firmalarKeys.all });
}

export function useMeQuery(enabled = true) {
  return useQuery({
    queryKey: firmalarKeys.me(),
    queryFn: () => firmalarService.getMe(),
    enabled,
  });
}

export function useMeDashboardQuery(enabled = true) {
  return useQuery({
    queryKey: firmalarKeys.dashboard(),
    queryFn: () => firmalarService.getMeDashboard(),
    enabled,
  });
}

export function useOrgUnitsQuery(enabled = true) {
  return useQuery({
    queryKey: firmalarKeys.units(),
    queryFn: async () => {
      const page = await firmalarService.getOrgUnits();
      return page.results ?? [];
    },
    enabled,
  });
}

export function useOrgMembersQuery(orgId: number | string | null, enabled = true) {
  return useQuery({
    queryKey: firmalarKeys.unitMembers(orgId ?? ""),
    queryFn: async () => {
      const page = await firmalarService.getOrgMembers(orgId!);
      return page.results ?? [];
    },
    enabled: Boolean(orgId) && enabled,
  });
}

export function useApprovalsQuery(enabled = true) {
  return useQuery({
    queryKey: firmalarKeys.approvals(),
    queryFn: async () => {
      const page = await firmalarService.getApprovals();
      return page.results ?? [];
    },
    enabled,
  });
}

export function useInvitesQuery(enabled = true) {
  return useQuery({
    queryKey: firmalarKeys.invites(),
    queryFn: async () => {
      const page = await firmalarService.getInvites();
      return page.results ?? [];
    },
    enabled,
  });
}

export function useAddressesQuery(enabled = true) {
  return useQuery({
    queryKey: firmalarKeys.addresses(),
    queryFn: async () => {
      const page = await firmalarService.getAddresses();
      return page.results ?? [];
    },
    enabled,
  });
}

export function useCreateOrgUnitMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: OrgUnitCreateRequest) =>
      firmalarService.createOrgUnit(data),
    onSuccess: () => invalidateFirmalar(qc),
  });
}

export function useCreateInviteMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: InviteCreateRequest) =>
      firmalarService.createInvite(data),
    onSuccess: () => invalidateFirmalar(qc),
  });
}

export function useAddOrgMemberMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      orgId,
      data,
    }: {
      orgId: number | string;
      data: OrgMemberCreateRequest;
    }) => firmalarService.addOrgMember(orgId, data),
    onSuccess: () => invalidateFirmalar(qc),
  });
}

export function useCreateApprovalMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ApprovalCreateRequest) =>
      firmalarService.createApproval(data),
    onSuccess: () => invalidateFirmalar(qc),
  });
}

export function useSubmitApprovalMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number | string) => firmalarService.submitApproval(id),
    onSuccess: () => invalidateFirmalar(qc),
  });
}

export function useApproveApprovalMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number | string) => firmalarService.approveApproval(id),
    onSuccess: () => invalidateFirmalar(qc),
  });
}

export function useRejectApprovalMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number | string) => firmalarService.rejectApproval(id),
    onSuccess: () => invalidateFirmalar(qc),
  });
}

export function useCreateAddressMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FirmaAdresiCreateRequest) =>
      firmalarService.createAddress(data),
    onSuccess: () => invalidateFirmalar(qc),
  });
}
