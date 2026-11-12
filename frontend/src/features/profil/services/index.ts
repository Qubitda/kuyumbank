import {
  apiFetch,
  fetchMe,
  fetchMeDashboard,
  newIdempotencyKey,
} from "@/lib/api/client";
import type { MeDashboard, MeResponse } from "@/lib/api/types";
import type {
  DetailOk,
  FirmaAdresi,
  FirmaAdresiCreateRequest,
  FirmaAdresiPage,
  MeProfile,
  PasswordChangeRequest,
  ProfilePatchRequest,
} from "../types";

export const profilService = {
  getMe(): Promise<MeResponse> {
    return fetchMe();
  },
  getMeDashboard(): Promise<MeDashboard> {
    return fetchMeDashboard();
  },
  getProfile(): Promise<MeProfile> {
    return apiFetch<MeProfile>("/me/profile/");
  },
  updateProfile(data: ProfilePatchRequest): Promise<MeProfile> {
    return apiFetch<MeProfile>("/me/profile/", {
      method: "PATCH",
      body: data,
    });
  },
  changePassword(data: PasswordChangeRequest): Promise<DetailOk> {
    return apiFetch<DetailOk>("/auth/password-change/", {
      method: "POST",
      body: data,
    });
  },
  requestEmailVerify(email?: string): Promise<DetailOk> {
    return apiFetch<DetailOk>("/auth/email-verify/", {
      method: "POST",
      body: email ? { email } : {},
    });
  },
  confirmEmailVerify(data: { uid: string; token: string }): Promise<{
    detail: string;
    username: string;
    email_verified: boolean;
  }> {
    return apiFetch("/auth/email-verify/confirm/", {
      method: "POST",
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
  deleteAddress(id: number | string): Promise<void> {
    return apiFetch<void>(`/me/addresses/${id}/`, {
      method: "DELETE",
      idempotencyKey: newIdempotencyKey(),
    });
  },
};
