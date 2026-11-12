/**
 * Public API — auth (çapraz kesit; Django app değildir).
 * Dışarıdan yalnızca bu index üzerinden import edilir.
 */

export { LoginForm } from "./components/login-form";
export { SessionPanel } from "./components/session-panel";
export { DashboardCounters } from "./components/dashboard-counters";
export {
  AuthProvider,
  RequireAuth,
  useAuthContext,
} from "./components/auth-provider";
export { authService } from "./services/auth-service";
export { useAuth } from "./hooks/use-auth";
export { loginSchema, type LoginInput } from "./schemas/login";
export type {
  MeResponse,
  LoginResponse,
  ProblemDetail,
  AuthState,
} from "./types/auth";
