import type { MeResponse, ProblemDetail } from "@/lib/api/types";

export type { MeResponse, ProblemDetail };

export interface AuthState {
  user: MeResponse | null;
  loading: boolean;
  error: string | null;
}
