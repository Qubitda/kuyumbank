import type { CsrfResponse, MeResponse, ProblemDetail } from "./types";

const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly problem: ProblemDetail;

  constructor(problem: ProblemDetail) {
    super(problem.detail || problem.title || `HTTP ${problem.status}`);
    this.name = "ApiError";
    this.status = problem.status;
    this.problem = problem;
  }
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}=([^;]*)`),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

async function parseProblem(res: Response): Promise<ProblemDetail> {
  try {
    const body = (await res.json()) as Partial<ProblemDetail>;
    return {
      type: body.type,
      title: body.title,
      status: body.status ?? res.status,
      detail: body.detail,
      code: body.code,
      request_id: body.request_id,
    };
  } catch {
    return { status: res.status, title: res.statusText || "Hata" };
  }
}

/** NX-1: session cookie + CSRF; tarayıcıda Token yok. */
export async function ensureCsrfToken(): Promise<string> {
  const existing = readCookie("csrftoken");
  if (existing) return existing;
  const res = await fetch(`${API_PREFIX}/auth/csrf/`, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(await parseProblem(res));
  const data = (await res.json()) as CsrfResponse;
  return data.csrf_token;
}

type ApiFetchOptions = {
  method?: string;
  body?: unknown;
  idempotencyKey?: string;
};

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (method !== "GET" && method !== "HEAD") {
    headers["Content-Type"] = "application/json";
    headers["X-CSRFToken"] = await ensureCsrfToken();
  }
  if (options.idempotencyKey) {
    headers["Idempotency-Key"] = options.idempotencyKey;
  }

  const res = await fetch(`${API_PREFIX}${path}`, {
    method,
    credentials: "include",
    cache: "no-store",
    headers,
    body:
      options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (res.status === 204) return undefined as T;
  if (!res.ok) throw new ApiError(await parseProblem(res));
  return (await res.json()) as T;
}

export function login(username: string, password: string): Promise<MeResponse> {
  return apiFetch<MeResponse>("/auth/login/", {
    method: "POST",
    body: { username, password },
  });
}

export function logout(): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>("/auth/logout/", { method: "POST", body: {} });
}

export function fetchMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>("/me/");
}
