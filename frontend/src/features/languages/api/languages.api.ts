import { api } from '@/services/api';
import type {
  AddUserLanguageRequest,
  LanguageRef,
  UserLanguage,
  UserLanguagesResponse,
} from '../types/languages.types';

export const languagesApi = {
  getAll: (): Promise<LanguageRef[]> =>
    api.get('/languages'),
};

export function detectNativeLangId(languages: LanguageRef[]): number {
  const primaryCode = navigator.language.split('-')[0].toLowerCase();
  return (
    languages.find((l) => l.code === primaryCode)?.id ??
    languages.find((l) => l.code === 'en')?.id ??
    languages[0]?.id ??
    1
  );
}

export const userLanguagesApi = {
  getAll: (): Promise<UserLanguagesResponse> =>
    api.get('/users/me/languages'),

  add: (body: AddUserLanguageRequest): Promise<UserLanguage> =>
    api.post('/users/me/languages', body),

  activate: (languageId: number): Promise<UserLanguage> =>
    api.post(`/users/me/languages/${languageId}/activate`, {}),

  remove: (languageId: number): Promise<void> =>
    api.delete(`/users/me/languages/${languageId}`),
};
