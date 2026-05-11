import { api } from '@/services/api';
import type {
  LoginRequest,
  SignupRequest,
  PasswordChangeRequest,
  TokenResponse,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from '../types/auth.types';

export const authApi = {
  login: (body: LoginRequest) =>
    api.post<TokenResponse>('/auth/login', body),

  signup: (body: SignupRequest) =>
    api.post<TokenResponse>('/auth/signup', body),

  // POST /auth/logout is stateless (server just validates the token).
  // clearAuth() in the store does the real work client-side.
  logout: () => api.post<undefined>('/auth/logout'),

  changePassword: (body: PasswordChangeRequest) =>
    api.post<undefined>('/auth/change-password', body),

  verifyEmail: (token: string) =>
    api.post<{ message: string }>('/auth/verify-email', { token }),

  resendVerification: () =>
    api.post<undefined>('/auth/resend-verification'),

  forgotPassword: (body: ForgotPasswordRequest) =>
    api.post<undefined>('/auth/forgot-password', body),

  resetPassword: (body: ResetPasswordRequest) =>
    api.post<undefined>('/auth/reset-password', body),
};
