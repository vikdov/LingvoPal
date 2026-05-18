import { create } from 'zustand';
import { SESSION_HINT_KEY, USER_KEY, setAccessToken } from '@/services/api';
import type { User } from '../types/auth.types';

// ── Migration cleanup ─────────────────────────────────────────────────────────
// Remove tokens from localStorage that previous versions stored there.
localStorage.removeItem('lingvopal_token');
localStorage.removeItem('lingvopal_refresh_token');

// Read persisted user from localStorage without crashing on malformed JSON.
function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

const hasSession = !!localStorage.getItem(SESSION_HINT_KEY);
const storedUser = hasSession ? loadUser() : null;

// If there is no session hint, clear any stale user data.
if (!hasSession) {
  localStorage.removeItem(USER_KEY);
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  // Called after login / signup — sets in-memory access token and session hint.
  setAuth: (token: string, user: User) => void;
  // Called on logout or when api.ts throws UnauthorizedError.
  clearAuth: () => void;
  // Patch user fields in place (e.g. after profile update) without re-login.
  updateUser: (patch: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  user: storedUser,
  isAuthenticated: hasSession,

  setAuth: (token, user) => {
    setAccessToken(token);
    localStorage.setItem(SESSION_HINT_KEY, '1');
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ user, isAuthenticated: true });
  },

  clearAuth: () => {
    setAccessToken(null);
    localStorage.removeItem(SESSION_HINT_KEY);
    localStorage.removeItem(USER_KEY);
    set({ user: null, isAuthenticated: false });
  },

  updateUser: (patch) => {
    const current = get().user;
    if (!current) return;
    const updated = { ...current, ...patch };
    localStorage.setItem(USER_KEY, JSON.stringify(updated));
    set({ user: updated });
  },
}));
