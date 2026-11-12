import type {
  CsrfResponse,
  MeDashboard,
  MeResponse,
  Paginated,
  ProblemDetail,
} from "./types";

const API_PREFIX = "/api/v1";

export function newIdempotencyKey(): string {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

export function unwrapResults<T>(data: Paginated<T> | T[] | null | undefined): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.results ?? [];
}

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
    new RegExp(`(?:^|; )${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}=([^;]*)`)
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
      errors: body.errors,
    };
  } catch {
    return { status: res.status, title: res.statusText || "Sunucu Hatası" };
  }
}

/**
 * NX-1: session cookie + CSRF; tarayıcıda Token yok.
 */
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

export interface ApiFetchOptions {
  method?: string;
  body?: unknown;
  idempotencyKey?: string;
  headers?: Record<string, string>;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...options.headers,
  };

  const isMutating = method !== "GET" && method !== "HEAD";

  if (isMutating) {
    if (!headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    try {
      headers["X-CSRFToken"] = await ensureCsrfToken();
    } catch {
      // CSRF token alınamadıysa backend doğrulamasında 403 problem+json döner
    }
  }

  // Login ve logout dışındaki yazma isteklerinde Idempotency-Key
  if (isMutating && options.idempotencyKey) {
    headers["Idempotency-Key"] = options.idempotencyKey;
  }

  const res = await fetch(`${API_PREFIX}${path}`, {
    method,
    credentials: "include",
    cache: "no-store",
    headers,
    body:
      options.body === undefined
        ? undefined
        : typeof options.body === "string"
        ? options.body
        : JSON.stringify(options.body),
  });

  if (res.status === 204) {
    return undefined as T;
  }

  if (!res.ok) {
    throw new ApiError(await parseProblem(res));
  }

  return (await res.json()) as T;
}

export function login(username: string, password: string): Promise<MeResponse> {
  return apiFetch<MeResponse>("/auth/login/", {
    method: "POST",
    body: { username, password },
  });
}

export function logout(): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>("/auth/logout/", {
    method: "POST",
    body: {},
  });
}

export function fetchMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>("/me/");
}

export function fetchMeDashboard(): Promise<MeDashboard> {
  return apiFetch<MeDashboard>("/me/dashboard/");
}

/**
 * Same-origin binary/download helper (session cookie).
 * Yalnızca OpenAPI'de var olan path'ler için kullanın.
 */
export async function apiDownload(path: string, filename?: string): Promise<void> {
  const headers: Record<string, string> = { Accept: "*/*" };
  try {
    headers["X-CSRFToken"] = await ensureCsrfToken();
  } catch {
    // GET indirmede CSRF opsiyonel
  }

  const res = await fetch(`${API_PREFIX}${path}`, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
    headers,
  });

  if (!res.ok) {
    throw new ApiError(await parseProblem(res));
  }

  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition") || "";
  const match = /filename\*?=(?:UTF-8''|")?([^\";]+)/i.exec(cd);
  const name = filename || (match ? decodeURIComponent(match[1]) : `download-${Date.now()}`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
