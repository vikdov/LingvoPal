import { useQuery } from '@tanstack/react-query';
import { statsApi } from '../api/stats.api';

function isoToday() {
  return new Date().toISOString().slice(0, 10);
}
function isoNDaysAgo(n: number) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export const statKeys = {
  overview:      () => ['stats', 'overview'] as const,
  totals:        () => ['stats', 'totals']   as const,
  range:         (langId: number, start: string, end: string) =>
    ['stats', 'range', langId, start, end] as const,
  hardest:       (langId: number) => ['stats', 'hardest', langId] as const,
  vocabMaturity: (langId: number) => ['stats', 'vocab-maturity', langId] as const,
  setContext:    (setId: number) => ['stats', 'set-context', setId] as const,
};

export function useOverview() {
  return useQuery({
    queryKey: statKeys.overview(),
    queryFn:  statsApi.getOverview,
    staleTime: 60_000,
  });
}

export function useTotals() {
  return useQuery({
    queryKey: statKeys.totals(),
    queryFn:  statsApi.getTotals,
    staleTime: 60_000,
  });
}

// Fetches the last `days` days of activity for one language.
export function useRangeStats(languageId: number | null, days = 84) {
  const end   = isoToday();
  const start = isoNDaysAgo(days);
  return useQuery({
    queryKey: statKeys.range(languageId ?? 0, start, end),
    queryFn:  () => statsApi.getRangeStats(languageId!, start, end),
    enabled:  languageId != null && languageId > 0,
    staleTime: 60_000,
  });
}

export function useHardestItems(languageId: number | null) {
  return useQuery({
    queryKey: statKeys.hardest(languageId ?? 0),
    queryFn:  () => statsApi.getHardestItems(languageId!),
    enabled:  languageId != null && languageId > 0,
    staleTime: 60_000,
  });
}

export function useVocabMaturity(languageId: number | null) {
  return useQuery({
    queryKey: statKeys.vocabMaturity(languageId ?? 0),
    queryFn:  () => statsApi.getVocabMaturity(languageId!),
    enabled:  languageId != null && languageId > 0,
    staleTime: 120_000,
  });
}

export function useSetContext(setId: number | null) {
  return useQuery({
    queryKey: statKeys.setContext(setId ?? 0),
    queryFn:  () => statsApi.getSetContext(setId!),
    enabled:  setId != null && setId > 0,
    staleTime: 120_000,
  });
}
