import { api } from './api';

export interface Language {
  id: number;
  code: string;
  name: string;
}

export const languagesApi = {
  list: () => api.get<Language[]>('/languages'),
};

export function detectNativeLangId(languages: Language[]): number {
  const primaryCode = navigator.language.split('-')[0].toLowerCase();
  return (
    languages.find((l) => l.code === primaryCode)?.id ??
    languages.find((l) => l.code === 'en')?.id ??
    languages[0]?.id ??
    1
  );
}
