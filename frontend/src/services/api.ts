const BASE_URL = import.meta.env.VITE_API_URL as string;

export const TOKEN_KEY = 'lingvopal_token';
export const REFRESH_TOKEN_KEY = 'lingvopal_refresh_token';

// ── Error types ───────────────────────────────────────────────────────────────

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly extra: Record<string, unknown>;

  constructor(status: number, code: string, message: string, extra: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.extra = extra;
  }
}

// Thrown only when the stored token is expired/invalid — not for business-logic
// 401s like a wrong current password on change-password.
export class UnauthorizedError extends ApiError {
  constructor(message = 'Session expired. Please log in again.') {
    super(401, 'token_expired', message);
    this.name = 'UnauthorizedError';
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

// Backend wraps domain errors as { detail: { error: string, message: string } }.
// FastAPI validation errors use { detail: [...] }.
// FastAPI auth guard failures use { detail: "Could not validate credentials" }.
function parseDetail(detail: unknown): { code: string; message: string; extra: Record<string, unknown> } {
  if (typeof detail === 'string') {
    return { code: 'error', message: detail, extra: {} };
  }
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const d = detail as Record<string, unknown>;
    return {
      code: typeof d.error === 'string' ? d.error : 'unknown_error',
      message: typeof d.message === 'string' ? d.message : 'An error occurred',
      extra: d,
    };
  }
  return { code: 'unknown_error', message: 'An error occurred', extra: {} };
}

// Token-related error codes from the backend AuthErrorCode enum.
const TOKEN_ERROR_CODES = new Set(['token_expired', 'token_invalid']);

// ── Refresh token logic ───────────────────────────────────────────────────────

// Single in-flight refresh — concurrent 401s all wait on the same promise.
let _refreshPromise: Promise<string> | null = null;

async function _doRefresh(): Promise<string> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) throw new UnauthorizedError();

  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    throw new UnauthorizedError();
  }

  const data = await res.json() as { access_token: string; refresh_token: string };
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  return data.access_token;
}

async function tryRefresh(): Promise<string> {
  if (!_refreshPromise) {
    _refreshPromise = _doRefresh().finally(() => { _refreshPromise = null; });
  }
  return _refreshPromise;
}

// ── Core request ──────────────────────────────────────────────────────────────

async function _fetch(method: string, path: string, body?: unknown, headers?: Record<string, string>): Promise<Response> {
  const token = localStorage.getItem(TOKEN_KEY);
  const h: Record<string, string> = { 'Content-Type': 'application/json', ...headers };
  if (token) h['Authorization'] = `Bearer ${token}`;

  return fetch(`${BASE_URL}${path}`, {
    method,
    headers: h,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

async function request<T>(method: string, path: string, body?: unknown, _retry = true): Promise<T> {
  const res = await _fetch(method, path, body);

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({})) as Record<string, unknown>;

  if (!res.ok) {
    const { code, message, extra } = parseDetail(data.detail);

    if (res.status === 401) {
      const isSessionExpiry =
        typeof data.detail === 'string' || TOKEN_ERROR_CODES.has(code);

      if (isSessionExpiry) {
        // Try refresh once, then retry the original request.
        if (_retry && localStorage.getItem(REFRESH_TOKEN_KEY)) {
          try {
            await tryRefresh();
            return request<T>(method, path, body, false);
          } catch {
            // Refresh failed — clear everything, let providers clear React state.
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            throw new UnauthorizedError(typeof data.detail === 'string' ? undefined : message);
          }
        }
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        throw new UnauthorizedError(typeof data.detail === 'string' ? undefined : message);
      }
    }

    throw new ApiError(res.status, code, message, extra);
  }

  return data as T;
}

async function requestForm<T>(method: string, path: string, form: FormData): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { method, headers, body: form });

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({})) as Record<string, unknown>;

  if (!res.ok) {
    const { code, message } = parseDetail(data.detail);
    if (res.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      throw new UnauthorizedError(typeof data.detail === 'string' ? undefined : message);
    }
    throw new ApiError(res.status, code, message);
  }
  return data as T;
}

// ── Public API ────────────────────────────────────────────────────────────────

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
  postForm: <T>(path: string, form: FormData) => requestForm<T>('POST', path, form),
};

// rawPost: skip the 401-retry logic (used for /auth/refresh itself).
export async function rawPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await _fetch('POST', path, body);
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({})) as Record<string, unknown>;
  if (!res.ok) {
    const { code, message, extra } = parseDetail(data.detail);
    throw new ApiError(res.status, code, message, extra);
  }
  return data as T;
}
