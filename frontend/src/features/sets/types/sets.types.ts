// Mirrors backend ContentStatus enum
export type ContentStatus = 'DRAFT' | 'COMMUNITY' | 'APPROVED' | 'OFFICIAL';

// Mirrors backend PartOfSpeech enum
export type PartOfSpeech =
  | 'noun' | 'verb' | 'adjective' | 'adverb'
  | 'preposition' | 'conjunction'
  | 'phrase' | 'idiom' | 'phrasal_verb' | 'collocation';

export interface SetResponse {
  id: number;
  created_at: string;
  updated_at: string | null;
  title: string;
  description: string | null;
  difficulty: number | null;
  status: ContentStatus;
  creator_id: number | null;
  source_lang_id: number;
  target_lang_id: number | null;
  item_count: number;
  is_public: boolean;
}

export interface SetSummaryResponse {
  id: number;
  title: string;
  difficulty: number | null;
  status: ContentStatus;
  source_lang_id: number;
  target_lang_id: number | null;
  item_count: number;
}

export interface CreatedSetSummaryResponse extends SetSummaryResponse {
  is_pinned: boolean;
}

export interface SetLibraryEntry {
  set_id: number;
  added_at: string;
  last_opened_at: string | null;
  is_pinned: boolean;
  set: SetSummaryResponse;
}

export interface ItemSummaryResponse {
  id: number;
  term: string;
  language_id: number;
  context: string | null;
  difficulty: number | null;
  part_of_speech: PartOfSpeech | null;
  image_url: string | null;
  status: ContentStatus;
}

export interface TranslationResponse {
  id: number;
  created_at: string;
  updated_at: string | null;
  item_id: number;
  language_id: number;
  term_trans: string;
  context_trans: string | null;
  status: ContentStatus;
  creator_id: number | null;
  verified_by: number | null;
}

export interface ItemResponse {
  id: number;
  created_at: string;
  updated_at: string | null;
  term: string;
  language_id: number;
  context: string | null;
  difficulty: number | null;
  part_of_speech: PartOfSpeech | null;
  lemma: string | null;
  image_url: string | null;
  audio_url: string | null;
  context_audio_url: string | null;
  status: ContentStatus;
  creator_id: number | null;
  verified_by: number | null;
  is_public: boolean;
}

export interface ItemDetailResponse extends ItemResponse {
  translations: TranslationResponse[];
  translation_count: number;
}

export interface SetItemResponse {
  set_id: number;
  item_id: number;
  sort_order: number;
  item: ItemDetailResponse;
}

// ── Request types ────────────────────────────────────────────────────────────

export interface SetCreateRequest {
  title: string;
  description?: string;
  difficulty?: number;
  source_lang_id: number;
  target_lang_id?: number | null;
}

export interface SetUpdateRequest {
  title?: string;
  description?: string;
  difficulty?: number;
  source_lang_id?: number;
  target_lang_id?: number | null;
}

export interface ItemCreateRequest {
  term: string;
  language_id: number;
  context?: string;
  difficulty?: number;
  part_of_speech?: PartOfSpeech;
  lemma?: string;
  image_url?: string;
  audio_url?: string;
  context_audio_url?: string;
}

export interface ItemUpdateRequest {
  term?: string;
  context?: string | null;
  difficulty?: number | null;
  part_of_speech?: PartOfSpeech | null;
  lemma?: string | null;
  image_url?: string | null;
  audio_url?: string | null;
  context_audio_url?: string | null;
}

export interface TranslationCreateRequest {
  language_id: number;
  term_trans: string;
  context_trans?: string | null;
}

export interface TranslationUpdateRequest {
  term_trans?: string;
  context_trans?: string | null;
}
