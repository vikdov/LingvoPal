import { useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import i18n from '@/i18n/config';
import { settingsApi } from '../api/settings.api';
import { authApi } from '@/features/auth/api/auth.api';
import { useAuthStore } from '@/features/auth/store/auth.store';
import type { UserSettingsPatch, ProfilePatch } from '../types/settings.types';
import type { PasswordChangeRequest } from '@/features/auth/types/auth.types';

export const settingKeys = {
  all: ['settings'] as const,
  me: () => [...settingKeys.all, 'me'] as const,
  profile: () => ['profile', 'me'] as const,
};

export function useMySettings() {
  return useQuery({
    queryKey: settingKeys.me(),
    queryFn: settingsApi.getSettings,
    staleTime: Infinity,
  });
}

export function useInterfaceLanguage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { data: settings } = useMySettings();
  const code = settings?.interface_language?.code;

  useEffect(() => {
    if (isAuthenticated && code && i18n.language !== code) {
      i18n.changeLanguage(code);
    }
  }, [isAuthenticated, code]);
}

export function useMyProfile() {
  return useQuery({
    queryKey: settingKeys.profile(),
    queryFn: settingsApi.getProfile,
    staleTime: Infinity,
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: UserSettingsPatch) => settingsApi.patchSettings(patch),
    onSuccess: (data) => {
      qc.setQueryData(settingKeys.me(), data);
      const code = data.interface_language?.code;
      if (code && i18n.language !== code) {
        i18n.changeLanguage(code);
      }
    },
  });
}

export function useResetSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.resetSettings,
    onSuccess: (data) => {
      qc.setQueryData(settingKeys.me(), data);
    },
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  const updateUser = useAuthStore((s) => s.updateUser);
  return useMutation({
    mutationFn: (patch: ProfilePatch) => settingsApi.patchProfile(patch),
    onSuccess: (data) => {
      qc.setQueryData(settingKeys.profile(), data);
      updateUser({ username: data.username ?? undefined });
    },
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: settingsApi.deleteAccount,
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: authApi.resendVerification,
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (body: PasswordChangeRequest) => authApi.changePassword(body),
  });
}

export function useRequestEmailChange() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (new_email: string) => settingsApi.requestEmailChange(new_email),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingKeys.profile() });
    },
  });
}

export function useCancelEmailChange() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.cancelEmailChange,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingKeys.profile() });
    },
  });
}
