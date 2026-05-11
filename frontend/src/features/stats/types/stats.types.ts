// Matches get_overview() response shape
export interface LanguageOverview {
  language_id: number;
  language_code: string | null;
  language_name: string | null;
  streak_days: number;
  today_correct: number;
  today_incorrect: number;
  today_new_words: number;
  today_minutes: number;
}

export interface Overview {
  languages: LanguageOverview[];
  total_due_now: number;
}

// Matches get_total_stats() entries
export interface LanguageTotals {
  language_id: number;
  language_code: string | null;
  language_name: string | null;
  total_words_learned: number;
  total_hours: number;
  streak_days: number;
  last_recalculated_at: string | null;
}

// Matches _daily_to_dict() output
export interface DailyStats {
  stat_date: string;
  language_id: number;
  correct_count: number;
  incorrect_count: number;
  total_reviews: number;
  new_words_count: number;
  seconds_spent: number;
  accuracy_percent: number;
}

// Matches get_range_stats() response
export interface RangeStats {
  language_id: number;
  start_date: string;
  end_date: string;
  days_active: number;
  total_correct: number;
  total_incorrect: number;
  total_reviews: number;
  accuracy_percent: number;
  total_hours: number;
  avg_reviews_per_day: number;
  daily: DailyStats[];
}

export interface HardestItem {
  item_id: number;
  term: string;
  language_id: number;
  total_reviews: number;
  failure_rate: number;
}

export type MaturityKey = 'new' | 'learning' | 'young' | 'mature' | 'long_term';

export interface MaturityWord {
  item_id: number;
  term: string;
  interval: number;
}

export interface MaturityBucket {
  label: string;
  key: MaturityKey;
  range: string;
  count: number;
  percent: number;
  words: MaturityWord[];
}

export type SetMaturityKey = 'not_started' | MaturityKey;

export interface SetMaturityBucket {
  label: string;
  key: SetMaturityKey;
  count: number;
  percent: number;
}

export interface SetHardestWord {
  item_id: number;
  term: string;
  total_reviews: number;
  failure_rate: number;
}

export interface SetContext {
  set_id: number;
  total_items: number;
  practiced_items: number;
  practiced_percent: number;
  not_started: number;
  maturity_buckets: SetMaturityBucket[];
  hardest_words: SetHardestWord[];
}

export interface LearningBalance {
  status: 'heavy' | 'slow';
  message: string;
}

export interface VocabMaturity {
  total_items: number;
  buckets: MaturityBucket[];
  recently_mature: number;
  recently_long_term: number;
  new_this_month: number;
  learning_balance: LearningBalance | null;
}
