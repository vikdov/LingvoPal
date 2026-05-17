/**
 * Item suggestions API client.
 *
 * Communicates with POST /api/v1/items/suggestions to fetch:
 * - AI-enriched linguistic metadata
 * - TTS pronunciation audio
 * - Suggested reference images
 *
 * All returned values are suggestions only and remain editable by the user.
 */

import { api } from '@/services/api';

/* -------------------------------------------------------------------------- */
/*                                   Types                                    */
/* -------------------------------------------------------------------------- */

/**
 * Supported CEFR difficulty levels.
 */
export type CefrLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';

/**
 * Supported grammatical categories.
 *
 * Includes classical POS and language-learning-oriented expression types.
 */
export type PartOfSpeech =
  | 'noun'
  | 'verb'
  | 'adjective'
  | 'adverb'
  | 'preposition'
  | 'conjunction'
  | 'phrase'
  | 'idiom'
  | 'phrasal_verb'
  | 'collocation';

/**
 * Suggested translation.
 */
export interface TranslationSuggestion {
  /** Translated text */
  text: string;

  /** Translated context sentence with the translated term wrapped in {curly braces} */
  context_trans?: string;

  /** Optional language name/code */
  language?: string;
}

/**
 * Suggested image result.
 */
export interface ImageSuggestion {
  /** Full-size image URL */
  url: string;

  /** Optional thumbnail preview URL */
  thumbnail_url?: string;

  /** Optional image provider/source */
  source?: string;
}

/* -------------------------------------------------------------------------- */
/*                                   Request                                  */
/* -------------------------------------------------------------------------- */

/**
 * Request payload for AI-powered item metadata suggestions.
 */
export interface SuggestItemMetadataRequest {
  term: string;
  source_language: string;
  source_language_code: string;
  target_language?: string;
  /** User's existing context sentence — used for image search and context TTS */
  context?: string;
}

export interface GenerateAudioRequest {
  term: string;
  language_code: string;
  context?: string;
}

export interface GenerateAudioResponse {
  audio_url: string | null;
  context_audio_url: string | null;
}

/* -------------------------------------------------------------------------- */
/*                                  Response                                  */
/* -------------------------------------------------------------------------- */

/**
 * AI-generated metadata suggestions for a learning item.
 *
 * All fields are optional suggestions and can be:
 * - accepted
 * - edited
 * - removed
 * by the user before saving.
 */
export interface ItemMetadataSuggestion {
  /* ----------------------- Linguistic enrichment ----------------------- */

  /**
   * Canonical/base dictionary form.
   *
   * Example: "go" for "went"
   */
  lemma: string | null;

  /**
   * Grammatical category or expression type.
   */
  part_of_speech: PartOfSpeech | null;

  /**
   * Estimated CEFR difficulty level.
   */
  cefr_level: CefrLevel | null;

  /**
   * Short learner-friendly definition.
   */
  context: string | null;

  /**
   * Suggested translations.
   */
  translations: TranslationSuggestion[];

  /**
   * Related words or semantically similar expressions.
   */
  synonyms: string[];

  /* --------------------------------- Media -------------------------------- */

  /**
   * Generated pronunciation audio URL.
   */
  tts_audio_url: string | null;

  /**
   * Generated context sentence audio URL.
   */
  context_tts_audio_url: string | null;

  /**
   * Suggested visual reference images.
   */
  image_suggestions: ImageSuggestion[];
  /** Query used for image search — pass back to /search_images for more results */
  image_query: string | null;

  /* ------------------------------- Diagnostics ---------------------------- */

  /**
   * Optional non-fatal enrichment warnings.
   *
   * Examples:
   * - "tts_generation_failed"
   * - "image_search_failed"
   */
  warnings?: string[];
}

/* -------------------------------------------------------------------------- */
/*                                   API Call                                 */
/* -------------------------------------------------------------------------- */

/**
 * Fetch AI-generated suggestions for a learning item.
 *
 * Backend enrichment pipeline may run in parallel:
 * - AI linguistic enrichment
 * - TTS generation
 * - image search
 *
 * Partial failures are tolerated.
 */
export async function suggestItemMetadata(
  request: SuggestItemMetadataRequest,
): Promise<ItemMetadataSuggestion> {
  return api.post('/items/suggestions', request);
}

export async function generateItemAudio(
  request: GenerateAudioRequest,
): Promise<GenerateAudioResponse> {
  return api.post('/items/generate_audio', request);
}

export interface SearchImagesRequest {
  query: string;
  count?: number;
}

export async function searchItemImages(
  request: SearchImagesRequest,
): Promise<ImageSuggestion[]> {
  return api.post('/items/search_images', request);
}

/* -------------------------------------------------------------------------- */
/*                                  Re-exports                                */
/* -------------------------------------------------------------------------- */

export type {
  SuggestItemMetadataRequest as ItemSuggestionRequest,
  ItemMetadataSuggestion as ItemSuggestion,
};
