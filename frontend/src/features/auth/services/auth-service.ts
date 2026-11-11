import { apiFetch, login as apiLogin, logout as apiLogout, fetchMe as apiFetchMe } from "@/lib/api/client";
import type { MeResponse, CsrfResponse } from "@/lib/api/types";

export const authService = {
  getCsrfToken(): Promise<CsrfResponse> {
    return apiFetch<CsrfResponse>("/auth/csrf/");
  },
  login(username: string, password: string): Promise<MeResponse> {
    return apiLogin(username, password);
  },
  logout(): Promise<{ ok: boolean }> {
    return apiLogout();
  },
  getMe(): Promise<MeResponse> {
    return apiFetchMe();
  },
};
