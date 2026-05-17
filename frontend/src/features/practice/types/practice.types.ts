export type EvaluationMode = 'strict' | 'normal' | 'forgiving';

export interface ComparisonConfig {
  evaluation_mode: EvaluationMode;
  show_hints_on_fails: boolean;
  show_translations: boolean;
  show_images: boolean;
  show_synonyms: boolean;
  show_part_of_speech: boolean;
  auto_play_audio: boolean;
}

// One item in the practice batch — everything the frontend needs to render a card.
// answer = item.term (what user types); prompt = translation (shown as hint).
export interface ItemHint {
  item_id: number;
  answer: string;
  prompt: string;
  context: string | null;
  context_trans: string | null;
  image_url: string | null;
  audio_url: string | null;
  context_audio_url: string | null;
  part_of_speech: string | null;
  synonyms: string[];
  last_reviewed: string | null;
  translation_id: number | null;
  creator_id: number | null;
  item_status: string;
  // Cloze split — provided as strings to avoid Python code-point vs JS UTF-16 mismatch
  cloze_prefix: string | null;
  cloze_word: string | null;
  cloze_suffix: string | null;
}

export interface SessionStarted {
  session_id: number;
  set_id: number | null;
  items: ItemHint[];
  comparison_config: ComparisonConfig;
  current_index: number;
  resumed: boolean;
}

export interface SubmitAnswerRequest {
  answer_id: string;
  item_id: number;
  user_answer: string;
  response_time_ms: number;
  confidence_override?: number;
}

export interface AnswerBufferedResponse {
  buffered: boolean;
  remaining_count: number;
  is_batch_complete: boolean;
  is_correct: boolean;
  similarity: number;
}

export interface SessionSummary {
  session_id: number;
  status: string;
  total_reviewed: number;
  correct_count: number;
  accuracy: number;
  avg_response_ms: number;
  leech_item_ids: number[];
}

export interface ActiveSession {
  has_active_session: boolean;
  session_id?: number;
  set_id?: number;
  remaining_count?: number;
}

// UI-only lifecycle — drives visual state; is_correct is the backend truth for SM-2.
// 'corrected' = initially wrong, user successfully retyped the correct answer.
// 'unanswered' is intentionally kept for exhaustive switch statements in components.
export type AnswerLifecycle = 'unanswered' | 'correct' | 'retrying' | 'corrected';

// Frontend-only: recorded result for one answered item.
// lifecycle is UI-only; is_correct is never changed after the first backend response.
export interface AnswerRecord {
  itemId: number;
  userAnswer: string;
  isCorrect: boolean;
  similarity: number;
  responseTimeMs: number;
  lifecycle: AnswerLifecycle;
  confidenceOverride: number | null;
}

// 'feedback' removed — visual state derives from AnswerRecord.lifecycle.
// 'answering' renamed to 'active' — phase no longer encodes per-item interaction state.
export type SessionPhase =
  | 'idle'
  | 'loading'
  | 'active'
  | 'no_due_items'
  | 'finalising'
  | 'complete'
  | 'error';
