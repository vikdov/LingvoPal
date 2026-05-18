export type EvaluationMode = 'strict' | 'normal' | 'forgiving';
export type LearningIntensity = 'light' | 'balanced' | 'intensive';
export type RetentionPriority = 'speed_learning' | 'balanced' | 'long_term_mastery';

export interface LanguageRef {
  id: number;
  code: string;
  name: string;
}

export interface UserSettings {
  user_id: number;
  native_language: LanguageRef;
  interface_language: LanguageRef;
  learning_intensity: LearningIntensity;
  evaluation_mode: EvaluationMode;
  show_hints_on_fails: boolean;
  daily_study_goal: number;
  reminder_time: string | null;
  streak_reminders_enabled: boolean;
  show_translations: boolean;
  show_images: boolean;
  show_synonyms: boolean;
  show_part_of_speech: boolean;
  auto_play_audio: boolean;
  new_items_per_day_limit: number;
  new_items_per_session: number;
  retention_priority: RetentionPriority;
  max_review_load_per_day: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface UserSettingsPatch {
  native_lang_id?: number;
  interface_lang_id?: number;
  learning_intensity?: LearningIntensity;
  evaluation_mode?: EvaluationMode;
  show_hints_on_fails?: boolean;
  daily_study_goal?: number;
  streak_reminders_enabled?: boolean;
  show_translations?: boolean;
  show_images?: boolean;
  show_synonyms?: boolean;
  show_part_of_speech?: boolean;
  auto_play_audio?: boolean;
  reminder_time?: string | null;
  new_items_per_day_limit?: number;
  new_items_per_session?: number;
  retention_priority?: RetentionPriority;
  max_review_load_per_day?: number | null;
}

export interface UserProfile {
  id: number;
  username: string | null;
  email: string;
  email_verified: boolean;
  pending_email: string | null;
  is_admin: boolean;
  created_at: string;
  deleted_at: string | null;
}

export interface ProfilePatch {
  username?: string;
}
