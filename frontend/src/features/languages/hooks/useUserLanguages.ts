import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { languagesApi, userLanguagesApi } from '../api/languages.api';
import { useLanguageStore } from '../store/language.store';
import type { AddUserLanguageRequest } from '../types/languages.types';

export const languageKeys = {
  all: ['languages'] as const,
};

export const userLanguageKeys = {
  all: ['user-languages'] as const,
};

export function useAllLanguages() {
  return useQuery({
    queryKey: languageKeys.all,
    queryFn: () => languagesApi.getAll(),
    staleTime: Infinity,
  });
}

export function useUserLanguages() {
  const setActiveFromServer = useLanguageStore((s) => s.setActiveFromServer);

  return useQuery({
    queryKey: userLanguageKeys.all,
    queryFn: async () => {
      const data = await userLanguagesApi.getAll();
      if (data.active_language) {
        setActiveFromServer(data.active_language.id);
      }
      return data;
    },
    staleTime: Infinity,
  });
}

export function useAddUserLanguage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: AddUserLanguageRequest) => userLanguagesApi.add(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: userLanguageKeys.all }),
  });
}

export function useActivateLanguage() {
  const qc = useQueryClient();
  const setActive = useLanguageStore((s) => s.setActive);

  return useMutation({
    mutationFn: (languageId: number) => userLanguagesApi.activate(languageId),
    onSuccess: (row) => {
      setActive(row.language.id);
      qc.invalidateQueries({ queryKey: userLanguageKeys.all });
    },
  });
}

export function useRemoveUserLanguage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (languageId: number) => userLanguagesApi.remove(languageId),
    onSuccess: () => qc.invalidateQueries({ queryKey: userLanguageKeys.all }),
  });
}
