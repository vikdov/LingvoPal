import { create } from 'zustand';
import { TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/services/api';
import type { User } from '../types/auth.types';

const USER_KEY = 'lingvopal_user';

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return typeof payload.exp === 'number' && payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

// Read persisted user from localStorage without crashing on malformed JSON.
function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

// Eagerly validate token on boot — clear stale data before any React renders.
const storedToken = localStorage.getItem(TOKEN_KEY);
const validToken = storedToken && !isTokenExpired(storedToken) ? storedToken : null;
// If access token is expired but refresh token exists, keep user logged in —
// api.ts will handle auto-refresh on first request.
const hasRefreshToken = !!localStorage.getItem(REFRESH_TOKEN_KEY);
if (!validToken && !hasRefreshToken) {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  // Called after login / signup — persists to localStorage so api.ts can read the token.
  setAuth: (token: string, refreshToken: string, user: User) => void;
  // Called on logout or when api.ts throws UnauthorizedError.
  clearAuth: () => void;
  // Patch user fields in place (e.g. after profile update) without re-login.
  updateUser: (patch: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  token: validToken,
  user: (validToken || hasRefreshToken) ? loadUser() : null,
  isAuthenticated: !!(validToken || hasRefreshToken),

  setAuth: (token, refreshToken, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },

  clearAuth: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({ token: null, user: null, isAuthenticated: false });
  },

  updateUser: (patch) => {
    const current = get().user;
    if (!current) return;
    const updated = { ...current, ...patch };
    localStorage.setItem(USER_KEY, JSON.stringify(updated));
    set({ user: updated });
  },
}));
