// Mirrors backend UserAuthResponse
export interface User {
  id: number;
  username: string | null;
  email: string;
  email_verified: boolean;
  is_admin: boolean;
  created_at: string;
  native_lang_id: number;
  active_target_lang_id: number | null;
}

// Mirrors backend TokenResponse
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Mirrors backend request schemas
export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  username: string;
  native_lang_id: number;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}
