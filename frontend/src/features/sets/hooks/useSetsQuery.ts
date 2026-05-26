import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { setsApi } from '../api/sets.api';
import type {
  CreatedSetSummaryResponse,
  SetCreateRequest,
  SetLibraryEntry,
  SetUpdateRequest,
  ItemCreateRequest,
  ItemUpdateRequest,
  TranslationCreateRequest,
  TranslationUpdateRequest,
  PartOfSpeech,
} from '../types/sets.types';
import type { PaginatedResponse } from '@/types/common.types';
import type { ComplaintReason } from '@/features/admin/types/admin.types';

export const setKeys = {
  all:           () => ['sets'] as const,
  library:       (skip: number, limit: number) => ['sets', 'library', skip, limit] as const,
  libraryStatus: (id: number) => ['sets', id, 'library-status'] as const,
  createdSets:   (skip: number, limit: number) => ['sets', 'created', skip, limit] as const,
  set:           (id: number) => ['sets', id] as const,
  items:         (id: number, params?: { skip: number; limit: number }) =>
    params ? ['sets', id, 'items', params] as const : ['sets', id, 'items'] as const,
  public:        (params: object) => ['sets', 'public', params] as const,
};

export const moderationKeys = {
  mySubmissions: (skip: number, limit: number) => ['moderation', 'my', skip, limit] as const,
  latestSet:     (setId: number) => ['moderation', 'set', setId, 'latest'] as const,
  latestItem:    (itemId: number) => ['moderation', 'item', itemId, 'latest'] as const,
};

export const itemKeys = {
  public:   (params: object) => ['items', 'public', params] as const,
  mine:     (skip: number, limit: number) => ['items', 'mine', skip, limit] as const,
  detail:   (itemId: number) => ['items', itemId] as const,
  synonyms: (itemId: number) => ['items', itemId, 'synonyms'] as const,
};

export function useMyLibrary(skip = 0, limit = 20) {
  return useQuery({
    queryKey: setKeys.library(skip, limit),
    queryFn:  () => setsApi.getLibrary(skip, limit),
    staleTime: 60_000,
  });
}

export function useCreatedSets(skip = 0, limit = 20) {
  return useQuery({
    queryKey: setKeys.createdSets(skip, limit),
    queryFn:  () => setsApi.getCreatedSets(skip, limit),
    staleTime: 60_000,
  });
}

export function useSet(setId: number) {
  return useQuery({
    queryKey: setKeys.set(setId),
    queryFn:  () => setsApi.getSet(setId),
    enabled:  setId > 0,
    staleTime: 60_000,
  });
}

export function useSetItems(setId: number, skip = 0, limit = 20) {
  return useQuery({
    queryKey: setKeys.items(setId, { skip, limit }),
    queryFn:  () => setsApi.getSetItems(setId, skip, limit),
    enabled:  setId > 0,
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

export function usePublicSets(params: {
  query?: string;
  target_lang_id?: number | null;
  source_lang_id?: number | null;
  difficulty?: number | null;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: setKeys.public(params),
    queryFn:  () => setsApi.getPublicSets(params),
    staleTime: 60_000,
  });
}

// ── Mutations ─────────────────────────────────────────────────────────────────

export function useCreateSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SetCreateRequest) => setsApi.createSet(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
    },
  });
}

export function useUpdateSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, body }: { setId: number; body: SetUpdateRequest }) =>
      setsApi.updateSet(setId, body),
    onSuccess: (_data, { setId }) => {
      qc.invalidateQueries({ queryKey: setKeys.set(setId) });
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
    },
  });
}

export function useDeleteSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (setId: number) => setsApi.deleteSet(setId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
    },
  });
}

export function useTouchSet() {
  const qc = useQueryClient();

  function moveToFront<T extends { is_pinned?: boolean }>(items: T[], id: number, idKey: keyof T): T[] {
    const idx = items.findIndex((e) => e[idKey] === id);
    if (idx <= 0) return items;
    const item = items[idx];
    const rest = items.filter((_, i) => i !== idx);
    const pinned = rest.filter((e) => e.is_pinned);
    const unpinned = rest.filter((e) => !e.is_pinned);
    return item.is_pinned
      ? [item, ...pinned, ...unpinned]
      : [...pinned, item, ...unpinned];
  }

  return useMutation({
    mutationFn: (setId: number) => setsApi.touchSet(setId),
    onMutate: (setId) => {
      qc.setQueriesData<PaginatedResponse<SetLibraryEntry>>(
        { queryKey: ['sets', 'library'] },
        (old) => old?.data ? { ...old, data: moveToFront(old.data, setId, 'set_id') } : old,
      );
      qc.setQueriesData<PaginatedResponse<CreatedSetSummaryResponse>>(
        { queryKey: ['sets', 'created'] },
        (old) => old?.data ? { ...old, data: moveToFront(old.data, setId, 'id') } : old,
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
    },
  });
}

export function usePinSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, is_pinned }: { setId: number; is_pinned: boolean }) =>
      setsApi.updateLibraryPin(setId, is_pinned),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
    },
  });
}

export function useIsInLibrary(setId: number) {
  return useQuery({
    queryKey: setKeys.libraryStatus(setId),
    queryFn: () => setsApi.getLibraryStatus(setId),
    enabled: setId > 0,
    staleTime: 60_000,
    select: (data) => data.in_library,
  });
}

export function useAddToLibrary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (setId: number) => setsApi.addToLibrary(setId),
    onSuccess: (_data, setId) => {
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
      qc.setQueryData(setKeys.libraryStatus(setId), { in_library: true });
    },
  });
}

export function useRemoveFromLibrary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (setId: number) => setsApi.removeFromLibrary(setId),
    onSuccess: (_data, setId) => {
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
      qc.setQueryData(setKeys.libraryStatus(setId), { in_library: false });
    },
  });
}

export function useLatestSetModeration(setId: number) {
  return useQuery({
    queryKey: moderationKeys.latestSet(setId),
    queryFn: () => setsApi.getLatestSetModeration(setId),
    enabled: setId > 0,
    staleTime: 30_000,
  });
}

export function useLatestItemModeration(itemId: number | null) {
  return useQuery({
    queryKey: moderationKeys.latestItem(itemId ?? 0),
    queryFn: () => setsApi.getLatestItemModeration(itemId!),
    enabled: !!itemId,
    staleTime: 30_000,
  });
}

export function useMySubmissions(skip = 0, limit = 20) {
  return useQuery({
    queryKey: moderationKeys.mySubmissions(skip, limit),
    queryFn: () => setsApi.getMySubmissions(skip, limit),
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

export function useForkSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (setId: number) => setsApi.forkSet(setId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
    },
  });
}

export function useUploadItemImage(setId?: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, file }: { itemId: number; file: File }) =>
      setsApi.uploadItemImage(itemId, file),
    onSuccess: () => {
      if (setId) qc.invalidateQueries({ queryKey: setKeys.items(setId) });
    },
  });
}

export function useUploadItemAudio(setId?: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, file }: { itemId: number; file: File }) =>
      setsApi.uploadItemAudio(itemId, file),
    onSuccess: () => {
      if (setId) qc.invalidateQueries({ queryKey: setKeys.items(setId) });
    },
  });
}

export function useUploadItemContextAudio(setId?: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, file }: { itemId: number; file: File }) =>
      setsApi.uploadItemContextAudio(itemId, file),
    onSuccess: () => {
      if (setId) qc.invalidateQueries({ queryKey: setKeys.items(setId) });
    },
  });
}

export function useCreateItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, body }: { setId: number; body: ItemCreateRequest }) =>
      setsApi.createItem(setId, body),
    onSuccess: (_data, { setId }) => {
      qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      qc.invalidateQueries({ queryKey: setKeys.set(setId) });
    },
  });
}

export function useUpdateItem(setId?: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, body }: { itemId: number; body: ItemUpdateRequest }) =>
      setsApi.updateItem(itemId, body),
    onSuccess: () => {
      if (setId) {
        qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      }
    },
  });
}

export function useRemoveItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, itemId }: { setId: number; itemId: number }) =>
      setsApi.removeItem(setId, itemId),
    onSuccess: (_data, { setId }) => {
      qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      qc.invalidateQueries({ queryKey: setKeys.set(setId) });
    },
  });
}

export function useCreateTranslation(setId?: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, body }: { itemId: number; body: TranslationCreateRequest }) =>
      setsApi.createTranslation(itemId, body),
    onSuccess: () => {
      if (setId) {
        qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      } else {
        qc.invalidateQueries({ queryKey: ['sets'] });
      }
    },
  });
}

export function useUpdateTranslation(setId?: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      translationId,
      body,
    }: {
      itemId: number;
      translationId: number;
      body: TranslationUpdateRequest;
    }) => setsApi.updateTranslation(itemId, translationId, body),
    onSuccess: () => {
      if (setId) {
        qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      }
    },
  });
}

export function useDeleteTranslation(setId?: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      translationId,
    }: {
      itemId: number;
      translationId: number;
    }) => setsApi.deleteTranslation(itemId, translationId),
    onSuccess: () => {
      if (setId) {
        qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      }
    },
  });
}

export function usePublicItems(params: {
  query?: string;
  language_id?: number | null;
  part_of_speech?: PartOfSpeech | null;
  difficulty?: number | null;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: itemKeys.public(params),
    queryFn: () =>
      setsApi.searchPublicItems({
        query: params.query || undefined,
        language_id: params.language_id ?? undefined,
        part_of_speech: params.part_of_speech ?? undefined,
        difficulty: params.difficulty ?? undefined,
        skip: params.skip,
        limit: params.limit,
      }),
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

export function useAddExistingItemToSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, itemId }: { setId: number; itemId: number }) =>
      setsApi.addExistingItemToSet(setId, itemId),
    onSuccess: (_data, { setId }) => {
      qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      qc.invalidateQueries({ queryKey: setKeys.set(setId) });
    },
  });
}

export function useForkItemIntoSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, itemId }: { setId: number; itemId: number }) =>
      setsApi.forkItemIntoSet(setId, itemId),
    onSuccess: (_data, { setId }) => {
      qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      qc.invalidateQueries({ queryKey: setKeys.set(setId) });
    },
  });
}

/** @deprecated Alias for useCreatedSets — kept for backward compat */
export function useMySets(skip = 0, limit = 20) {
  return useCreatedSets(skip, limit);
}

export function useMyItems(skip = 0, limit = 20, query?: string) {
  return useQuery({
    queryKey: [...itemKeys.mine(skip, limit), query ?? ''],
    queryFn: () => setsApi.getMyItems(skip, limit, query),
    staleTime: 60_000,
    placeholderData: (prev) => prev,
  });
}

export function useItemDetail(itemId: number | null) {
  return useQuery({
    queryKey: itemKeys.detail(itemId ?? 0),
    queryFn: () => setsApi.getItem(itemId!),
    enabled: itemId != null,
    staleTime: 60_000,
  });
}

export function useDeleteItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: number) => setsApi.deleteItem(itemId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['items', 'mine'] }),
  });
}

export function useReportItem() {
  return useMutation({
    mutationFn: ({ itemId, reason, details }: { itemId: number; reason: ComplaintReason; details?: string }) =>
      setsApi.reportItem(itemId, { reason, details }),
  });
}

export function useReportSet() {
  return useMutation({
    mutationFn: ({ setId, reason, details }: { setId: number; reason: ComplaintReason; details?: string }) =>
      setsApi.reportSet(setId, { reason, details }),
  });
}

export function useItemSynonyms(itemId: number | undefined) {
  return useQuery({
    queryKey: itemKeys.synonyms(itemId ?? 0),
    queryFn: () => setsApi.getItemSynonyms(itemId!),
    enabled: !!itemId,
    staleTime: 30_000,
  });
}

export function useSetSynonyms() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, terms }: { itemId: number; terms: string[] }) =>
      setsApi.setItemSynonyms(itemId, terms),
    onSuccess: (_data, { itemId }) => {
      qc.invalidateQueries({ queryKey: itemKeys.synonyms(itemId) });
    },
  });
}

export function useSynonymSuggestions(languageId: number | null, q: string) {
  return useQuery({
    queryKey: ['synonym-suggestions', languageId, q],
    queryFn: () => setsApi.getSynonymSuggestions(languageId!, q),
    enabled: !!languageId && q.trim().length > 0,
    staleTime: 60_000,
  });
}

export function useSubmitSetForReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, feedback }: { setId: number; feedback?: string }) =>
      setsApi.submitSetForReview(setId, feedback),
    onSuccess: (_data, { setId }) => {
      qc.invalidateQueries({ queryKey: setKeys.set(setId) });
      qc.invalidateQueries({ queryKey: moderationKeys.latestSet(setId) });
      qc.invalidateQueries({ queryKey: ['moderation', 'my'] });
    },
  });
}

export function useSubmitItemForReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, feedback }: { itemId: number; feedback?: string }) =>
      setsApi.submitItemForReview(itemId, feedback),
    onSuccess: (_data, { itemId }) => {
      qc.invalidateQueries({ queryKey: itemKeys.detail(itemId) });
      qc.invalidateQueries({ queryKey: ['sets'] });
    },
  });
}

export function useExportSet() {
  return useMutation({
    mutationFn: ({ setId, title }: { setId: number; title: string }) =>
      setsApi.exportSet(setId, title),
  });
}
