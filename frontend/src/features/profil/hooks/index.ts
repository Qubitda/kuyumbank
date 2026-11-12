"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profilService } from "../services";
import type {
  FirmaAdresiCreateRequest,
  PasswordChangeRequest,
  ProfilePatchRequest,
} from "../types";

export const profilKeys = {
  all: ["profil"] as const,
  profile: () => [...profilKeys.all, "profile"] as const,
  addresses: () => [...profilKeys.all, "addresses"] as const,
  dashboard: () => [...profilKeys.all, "dashboard"] as const,
};

function invalidateProfil(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: profilKeys.all });
}

export function useProfileQuery(enabled = true) {
  return useQuery({
    queryKey: profilKeys.profile(),
    queryFn: () => profilService.getProfile(),
    enabled,
  });
}

export function useProfileAddressesQuery(enabled = true) {
  return useQuery({
    queryKey: profilKeys.addresses(),
    queryFn: async () => {
      const page = await profilService.getAddresses();
      return page.results ?? [];
    },
    enabled,
  });
}

export function useProfileDashboardQuery(enabled = true) {
  return useQuery({
    queryKey: profilKeys.dashboard(),
    queryFn: () => profilService.getMeDashboard(),
    enabled,
  });
}

export function useUpdateProfileMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfilePatchRequest) =>
      profilService.updateProfile(data),
    onSuccess: () => invalidateProfil(qc),
  });
}

export function useChangePasswordMutation() {
  return useMutation({
    mutationFn: (data: PasswordChangeRequest) =>
      profilService.changePassword(data),
  });
}

export function useCreateProfileAddressMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FirmaAdresiCreateRequest) =>
      profilService.createAddress(data),
    onSuccess: () => invalidateProfil(qc),
  });
}

export function useDeleteProfileAddressMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number | string) => profilService.deleteAddress(id),
    onSuccess: () => invalidateProfil(qc),
  });
}
