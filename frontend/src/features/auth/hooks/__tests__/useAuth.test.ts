import { renderHook, act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../api/auth.api', () => ({
  authApi: {
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
    changePassword: vi.fn(),
  },
}));

const mockSetAuth = vi.fn();
const mockClearAuth = vi.fn();
const mockStore = {
  token: null as string | null,
  user: null as null | object,
  isAuthenticated: false,
  setAuth: mockSetAuth,
  clearAuth: mockClearAuth,
};

vi.mock('../../store/auth.store', () => ({
  useAuthStore: (selector: (s: typeof mockStore) => unknown) => selector(mockStore),
}));

import { useAuth } from '../useAuth';
import { authApi } from '../../api/auth.api';

const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  email_verified: true,
  is_admin: false,
  created_at: '2024-01-01T00:00:00Z',
  native_lang_id: 1,
  active_target_lang_id: null,
};

beforeEach(() => {
  mockStore.user = null;
  mockStore.isAuthenticated = false;
  vi.clearAllMocks();
  mockSetAuth.mockImplementation((token: string, user: object) => {
    mockStore.token = token;
    mockStore.user = user;
    mockStore.isAuthenticated = true;
  });
  mockClearAuth.mockImplementation(() => {
    mockStore.user = null;
    mockStore.isAuthenticated = false;
  });
});

describe('useAuth', () => {
  it('returns unauthenticated state by default', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('login calls api then setAuth', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'tok123',
      refresh_token: 'ref123',
      token_type: 'bearer',
      expires_in: 3600,
      user: mockUser,
    });

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      const user = await result.current.login({ email: 'test@example.com', password: 'pass' });
      expect(user).toEqual(mockUser);
    });

    expect(mockSetAuth).toHaveBeenCalledWith('tok123', 'ref123', mockUser);
  });

  it('signup calls api then setAuth', async () => {
    vi.mocked(authApi.signup).mockResolvedValue({
      access_token: 'tok456',
      refresh_token: 'ref456',
      token_type: 'bearer',
      expires_in: 3600,
      user: mockUser,
    });

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.signup({
        email: 'test@example.com',
        password: 'pass',
        username: 'testuser',
        native_lang_id: 1,
      });
    });

    expect(mockSetAuth).toHaveBeenCalledWith('tok456', 'ref456', mockUser);
  });

  it('logout clears auth even when server call fails', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network error'));

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.logout().catch(() => {});
    });

    expect(mockClearAuth).toHaveBeenCalled();
  });

  it('logout calls server then clears auth on success', async () => {
    vi.mocked(authApi.logout).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.logout();
    });

    expect(authApi.logout).toHaveBeenCalled();
    expect(mockClearAuth).toHaveBeenCalled();
  });

  it('changePassword delegates to api', async () => {
    vi.mocked(authApi.changePassword).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.changePassword({
        current_password: 'old',
        new_password: 'new',
      });
    });

    expect(authApi.changePassword).toHaveBeenCalledWith({
      current_password: 'old',
      new_password: 'new',
    });
  });
});
