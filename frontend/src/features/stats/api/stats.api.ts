import { api } from '@/services/api';
import type { Overview, LanguageTotals, DailyStats, RangeStats, HardestItem, VocabMaturity, SetContext } from '../types/stats.types';

export const statsApi = {
  getOverview: () =>
    api.get<Overview>('/stats/overview'),

  getTotals: () =>
    api.get<LanguageTotals[]>('/stats/totals'),

  getDailyStats: (languageId: number, page = 1, pageSize = 30) =>
    api.get<DailyStats[]>(`/stats/daily?language_id=${languageId}&page=${page}&page_size=${pageSize}`),

  getRangeStats: (languageId: number, startDate: string, endDate: string) =>
    api.get<RangeStats>(`/stats/range?language_id=${languageId}&start_date=${startDate}&end_date=${endDate}`),

  getStreak: (languageId: number) =>
    api.get<{ language_id: number; streak_days: number }>(`/stats/streak?language_id=${languageId}`),

  getHardestItems: (languageId: number, limit = 20) =>
    api.get<HardestItem[]>(`/stats/hardest-items?language_id=${languageId}&limit=${limit}`),

  getVocabMaturity: (languageId: number) =>
    api.get<VocabMaturity>(`/stats/vocab-maturity?language_id=${languageId}`),

  getSetContext: (setId: number) =>
    api.get<SetContext>(`/stats/set-context/${setId}`),
};
