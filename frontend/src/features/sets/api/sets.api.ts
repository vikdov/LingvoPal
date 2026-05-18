import { api } from '@/services/api';
import type { PaginatedResponse } from '@/types/common.types';
import type { ModerationSubmission } from '../types/sets.types';
import type {
  SetResponse,
  SetSummaryResponse,
  CreatedSetSummaryResponse,
  SetLibraryEntry,
  SetItemResponse,
  ItemSummaryResponse,
  ItemDetailResponse,
  TranslationResponse,
  SetCreateRequest,
  SetUpdateRequest,
  ItemCreateRequest,
  ItemUpdateRequest,
  TranslationCreateRequest,
  TranslationUpdateRequest,
} from '../types/sets.types';
import type { ComplaintRequest, ComplaintResponse } from '@/features/admin/types/admin.types';

export const setsApi = {
  // ── Sets ─────────────────────────────────────────────────────────────────
  getCreatedSets: (skip = 0, limit = 20) =>
    api.get<PaginatedResponse<CreatedSetSummaryResponse>>(`/sets/created?skip=${skip}&limit=${limit}`),

  touchSet: (setId: number) =>
    api.post<undefined>(`/sets/${setId}/touch`),

  updateLibraryPin: (setId: number, is_pinned: boolean) =>
    api.patch<undefined>(`/sets/${setId}/library`, { is_pinned }),

  getPublicSets: (params: {
    query?: string;
    target_lang_id?: number | null;
    source_lang_id?: number | null;
    difficulty?: number | null;
    skip?: number;
    limit?: number;
  } = {}) => {
    const qs = new URLSearchParams();
    if (params.query)                  qs.set('query',          params.query);
    if (params.target_lang_id != null) qs.set('target_lang_id', String(params.target_lang_id));
    if (params.source_lang_id != null) qs.set('source_lang_id', String(params.source_lang_id));
    if (params.difficulty != null)     qs.set('difficulty',     String(params.difficulty));
    if (params.skip != null)           qs.set('skip',           String(params.skip));
    if (params.limit != null)          qs.set('limit',          String(params.limit));
    return api.get<PaginatedResponse<SetSummaryResponse>>(`/sets/public?${qs}`);
  },

  getLibrary: (skip = 0, limit = 20) =>
    api.get<PaginatedResponse<SetLibraryEntry>>(`/sets/library?skip=${skip}&limit=${limit}`),

  addToLibrary: (setId: number) =>
    api.post<{ message: string }>(`/sets/${setId}/library`),

  removeFromLibrary: (setId: number) =>
    api.delete<undefined>(`/sets/${setId}/library`),

  forkSet: (setId: number) =>
    api.post<SetResponse>(`/sets/${setId}/fork`),

  getSet: (setId: number) =>
    api.get<SetResponse>(`/sets/${setId}`),

  createSet: (body: SetCreateRequest) =>
    api.post<SetResponse>('/sets', body),

  updateSet: (setId: number, body: SetUpdateRequest) =>
    api.patch<SetResponse>(`/sets/${setId}`, body),

  deleteSet: (setId: number) =>
    api.delete<undefined>(`/sets/${setId}`),

  // ── Items ─────────────────────────────────────────────────────────────────
  getSetItems: (setId: number, skip = 0, limit = 20) =>
    api.get<PaginatedResponse<SetItemResponse>>(`/sets/${setId}/items?skip=${skip}&limit=${limit}`),

  createItem: (setId: number, body: ItemCreateRequest) =>
    api.post<ItemDetailResponse>(`/sets/${setId}/items`, body),

  removeItem: (setId: number, itemId: number) =>
    api.delete<undefined>(`/sets/${setId}/items/${itemId}`),

  updateItem: (itemId: number, body: ItemUpdateRequest) =>
    api.patch<ItemDetailResponse>(`/items/${itemId}`, body),

  submitItem: (itemId: number) =>
    api.post<ItemDetailResponse>(`/items/${itemId}/submit`),

  uploadItemImage: (itemId: number, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.postForm<ItemDetailResponse>(`/items/${itemId}/image`, form);
  },

  uploadItemAudio: (itemId: number, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.postForm<ItemDetailResponse>(`/items/${itemId}/audio`, form);
  },

  uploadItemContextAudio: (itemId: number, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.postForm<ItemDetailResponse>(`/items/${itemId}/context_audio`, form);
  },

  searchPublicItems: (params: {
    query?: string;
    language_id?: number;
    part_of_speech?: string;
    difficulty?: number;
    skip?: number;
    limit?: number;
  } = {}) => {
    const qs = new URLSearchParams();
    if (params.query)         qs.set('query',          params.query);
    if (params.language_id)   qs.set('language_id',    String(params.language_id));
    if (params.part_of_speech) qs.set('part_of_speech', params.part_of_speech);
    if (params.difficulty)    qs.set('difficulty',     String(params.difficulty));
    if (params.skip != null)  qs.set('skip',           String(params.skip));
    if (params.limit != null) qs.set('limit',          String(params.limit));
    return api.get<PaginatedResponse<ItemSummaryResponse>>(`/items/public?${qs}`);
  },

  getMyItems: (skip = 0, limit = 20, query?: string) => {
    const qs = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (query) qs.set('query', query);
    return api.get<PaginatedResponse<ItemDetailResponse>>(`/items/mine?${qs}`);
  },

  getItem: (itemId: number) =>
    api.get<ItemDetailResponse>(`/items/${itemId}`),

  deleteItem: (itemId: number) =>
    api.delete<undefined>(`/items/${itemId}`),

  addExistingItemToSet: (setId: number, itemId: number) =>
    api.post<SetItemResponse>(`/sets/${setId}/items/${itemId}`),

  forkItemIntoSet: (setId: number, itemId: number) =>
    api.post<ItemDetailResponse>(`/sets/${setId}/items/${itemId}/fork`),

  // ── Translations ──────────────────────────────────────────────────────────
  createTranslation: (itemId: number, body: TranslationCreateRequest) =>
    api.post<TranslationResponse>(`/items/${itemId}/translations`, body),

  updateTranslation: (itemId: number, translationId: number, body: TranslationUpdateRequest) =>
    api.patch<TranslationResponse>(`/items/${itemId}/translations/${translationId}`, body),

  deleteTranslation: (itemId: number, translationId: number) =>
    api.delete<undefined>(`/items/${itemId}/translations/${translationId}`),

  submitTranslation: (itemId: number, translationId: number) =>
    api.post<TranslationResponse>(`/items/${itemId}/translations/${translationId}/submit`),

  reportItem: (itemId: number, body: ComplaintRequest) =>
    api.post<ComplaintResponse>(`/items/${itemId}/report`, body),

  reportSet: (setId: number, body: ComplaintRequest) =>
    api.post<ComplaintResponse>(`/sets/${setId}/report`, body),

  // ── Library status ────────────────────────────────────────────────────────
  getLibraryStatus: (setId: number) =>
    api.get<{ in_library: boolean }>(`/sets/${setId}/library`),

  // ── Moderation (user-facing submit) ──────────────────────────────────────
  submitSetForReview: (setId: number, feedback?: string) =>
    api.post<{ id: number; status: string }>(`/moderation/sets/${setId}/submit`, { feedback }),

  submitItemForReview: (itemId: number, feedback?: string) =>
    api.post<{ id: number; status: string }>(`/moderation/items/${itemId}/submit`, { feedback }),

  getLatestSetModeration: (setId: number) =>
    api.get<ModerationSubmission | null>(`/moderation/sets/${setId}/latest`),

  getLatestItemModeration: (itemId: number) =>
    api.get<ModerationSubmission | null>(`/moderation/items/${itemId}/latest`),

  getMySubmissions: (skip = 0, limit = 20) =>
    api.get<PaginatedResponse<ModerationSubmission>>(`/moderation/my?skip=${skip}&limit=${limit}`),

  // ── Synonyms ──────────────────────────────────────────────────────────────
  getItemSynonyms: (itemId: number) =>
    api.get<string[]>(`/items/${itemId}/synonyms`),

  setItemSynonyms: (itemId: number, terms: string[]) =>
    api.put<undefined>(`/items/${itemId}/synonyms`, { terms }),

  getSynonymSuggestions: (languageId: number, q: string) =>
    api.get<string[]>(`/items/synonym-suggestions?language_id=${languageId}&q=${encodeURIComponent(q)}`),
};
