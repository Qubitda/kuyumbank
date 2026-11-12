import {
  apiFetch,
  ensureCsrfToken,
  login as apiLogin,
  logout as apiLogout,
  fetchMe as apiFetchMe,
  verifyMfa as apiVerifyMfa,
  resendMfa as apiResendMfa,
} from "@/lib/api/client";
import type { CsrfResponse, LoginResponse, MeResponse } from "@/lib/api/types";

export const authService = {
  async ensureCsrf(): Promise<string> {
    return ensureCsrfToken();
  },
  getCsrfToken(): Promise<CsrfResponse> {
    return apiFetch<CsrfResponse>("/auth/csrf/");
  },
  async login(username: string, password: string): Promise<LoginResponse> {
    await ensureCsrfToken();
    return apiLogin(username, password);
  },
  logout(): Promise<{ ok: boolean }> {
    return apiLogout();
  },
  getMe(): Promise<MeResponse> {
    return apiFetchMe();
  },
  verifyMfa(code: string): Promise<MeResponse> {
    return apiVerifyMfa(code);
  },
  resendMfa(): Promise<{ detail?: string; mfa_ok?: boolean }> {
    return apiResendMfa();
  },
};
