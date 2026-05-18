import { useCallback } from 'react';
import { useAuthStore } from '../store/auth.store';
import { authApi } from '../api/auth.api';
import { useLanguageStore } from '@/features/languages';
import type {
  LoginRequest,
  SignupRequest,
  PasswordChangeRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from '../types/auth.types';

// Single hook for all auth actions. Components never touch the store or api directly.
export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setAuth = useAuthStore((s) => s.setAuth);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const login = useCallback(
    async (body: LoginRequest) => {
      const data = await authApi.login(body);
      setAuth(data.access_token, data.user);
      return data.user;
    },
    [setAuth],
  );

  const signup = useCallback(
    async (body: SignupRequest) => {
      const data = await authApi.signup(body);
      setAuth(data.access_token, data.user);
      return data.user;
    },
    [setAuth],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      clearAuth();
      useLanguageStore.getState().clear();
    }
  }, [clearAuth]);

  const changePassword = useCallback(
    async (body: PasswordChangeRequest) => {
      await authApi.changePassword(body);
    },
    [],
  );

  const verifyEmail = useCallback(async (token: string) => {
    await authApi.verifyEmail(token);
  }, []);

  const resendVerification = useCallback(async () => {
    await authApi.resendVerification();
  }, []);

  const forgotPassword = useCallback(async (body: ForgotPasswordRequest) => {
    await authApi.forgotPassword(body);
  }, []);

  const resetPassword = useCallback(async (body: ResetPasswordRequest) => {
    await authApi.resetPassword(body);
  }, []);

  return {
    user,
    isAuthenticated,
    login,
    signup,
    logout,
    changePassword,
    verifyEmail,
    resendVerification,
    forgotPassword,
    resetPassword,
  };
}
