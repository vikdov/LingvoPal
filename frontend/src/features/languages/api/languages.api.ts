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
