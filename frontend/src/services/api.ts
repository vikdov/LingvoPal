const BASE_URL = import.meta.env.VITE_API_URL as string;

// Persisted session hint — non-sensitive flag indicating an HttpOnly refresh
// cookie may exist. Allows the app to attempt a silent refresh on boot without
// storing the actual token value in localStorage.
export const SESSION_HINT_KEY = 'lingvopal_session';

// User profile key — non-sensitive, used for optimistic UI on page reload.
export const USER_KEY = 'lingvopal_user';

// ── In-memory access token ────────────────────────────────────────────────────
// Never persisted to storage. Lost on page close; recovered via silent refresh.

let _accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

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
  // The refresh token travels as an HttpOnly cookie — no body required.
  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!res.ok) {
    _accessToken = null;
    localStorage.removeItem(SESSION_HINT_KEY);
    localStorage.removeItem(USER_KEY);
    throw new UnauthorizedError();
  }

  const data = await res.json() as { access_token?: string };
  if (!data.access_token) {
    _accessToken = null;
    throw new UnauthorizedError('Refresh response missing access_token');
  }
  _accessToken = data.access_token;
  return data.access_token;
}

async function tryRefresh(): Promise<string> {
  if (!localStorage.getItem(SESSION_HINT_KEY)) throw new UnauthorizedError();
  if (!_refreshPromise) {
    _refreshPromise = _doRefresh().finally(() => { _refreshPromise = null; });
  }
  return _refreshPromise;
}

// ── Core request ──────────────────────────────────────────────────────────────

async function _fetch(method: string, path: string, body?: unknown, headers?: Record<string, string>): Promise<Response> {
  const h: Record<string, string> = { 'Content-Type': 'application/json', ...headers };
  if (_accessToken) h['Authorization'] = `Bearer ${_accessToken}`;

  return fetch(`${BASE_URL}${path}`, {
    method,
    headers: h,
    credentials: 'include',
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
        if (_retry && localStorage.getItem(SESSION_HINT_KEY)) {
          try {
            await tryRefresh();
            return request<T>(method, path, body, false);
          } catch {
            // Refresh failed — clear everything, let providers clear React state.
            _accessToken = null;
            localStorage.removeItem(SESSION_HINT_KEY);
            localStorage.removeItem(USER_KEY);
            throw new UnauthorizedError(typeof data.detail === 'string' ? undefined : message);
          }
        }
        _accessToken = null;
        localStorage.removeItem(SESSION_HINT_KEY);
        localStorage.removeItem(USER_KEY);
        throw new UnauthorizedError(typeof data.detail === 'string' ? undefined : message);
      }
    }

    throw new ApiError(res.status, code, message, extra);
  }

  return data as T;
}

async function requestBlob(method: string, path: string, _retry = true): Promise<Blob> {
  const h: Record<string, string> = {};
  if (_accessToken) h['Authorization'] = `Bearer ${_accessToken}`;

  const res = await fetch(`${BASE_URL}${path}`, { method, headers: h, credentials: 'include' });

  if (res.ok) return res.blob();

  if (res.status === 401 && _retry && localStorage.getItem(SESSION_HINT_KEY)) {
    try {
      await tryRefresh();
      return requestBlob(method, path, false);
    } catch {
      _accessToken = null;
      localStorage.removeItem(SESSION_HINT_KEY);
      localStorage.removeItem(USER_KEY);
      throw new UnauthorizedError();
    }
  }

  const data = await res.json().catch(() => ({})) as Record<string, unknown>;
  const { code, message, extra } = parseDetail(data.detail);
  throw new ApiError(res.status, code, message, extra);
}

async function requestForm<T>(method: string, path: string, form: FormData, _retry = true): Promise<T> {
  const headers: Record<string, string> = {};
  if (_accessToken) headers['Authorization'] = `Bearer ${_accessToken}`;

  const res = await fetch(`${BASE_URL}${path}`, { method, headers, credentials: 'include', body: form });

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({})) as Record<string, unknown>;

  if (!res.ok) {
    const { code, message } = parseDetail(data.detail);
    if (res.status === 401) {
      if (_retry && localStorage.getItem(SESSION_HINT_KEY)) {
        try {
          await tryRefresh();
          return requestForm<T>(method, path, form, false);
        } catch {
          _accessToken = null;
          localStorage.removeItem(SESSION_HINT_KEY);
          localStorage.removeItem(USER_KEY);
          throw new UnauthorizedError(typeof data.detail === 'string' ? undefined : message);
        }
      }
      _accessToken = null;
      localStorage.removeItem(SESSION_HINT_KEY);
      localStorage.removeItem(USER_KEY);
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
  getBlob: (path: string) => requestBlob('GET', path),
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
