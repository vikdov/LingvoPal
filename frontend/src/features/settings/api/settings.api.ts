import { api } from '@/services/api';
import type { UserSettings, UserSettingsPatch, UserProfile, ProfilePatch } from '../types/settings.types';

export const settingsApi = {
  getSettings: (): Promise<UserSettings> =>
    api.get('/settings/me'),

  patchSettings: (patch: UserSettingsPatch): Promise<UserSettings> =>
    api.patch('/settings/me', patch),

  resetSettings: (): Promise<UserSettings> =>
    api.post('/settings/reset', {}),

  getProfile: (): Promise<UserProfile> =>
    api.get('/users/me'),

  patchProfile: (patch: ProfilePatch): Promise<UserProfile> =>
    api.patch('/users/me', patch),

  deleteAccount: (): Promise<void> =>
    api.delete('/users/me'),
};
