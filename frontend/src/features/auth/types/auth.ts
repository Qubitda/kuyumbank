import type { LoginResponse, MeResponse, ProblemDetail } from "@/lib/api/types";

export type { MeResponse, LoginResponse, ProblemDetail };

export interface AuthState {
  user: MeResponse | null;
  loading: boolean;
  error: string | null;
  mfaPending: boolean;
  isAuthenticated: boolean;
}
