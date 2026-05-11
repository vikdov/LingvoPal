export type ModerationTargetType = 'item' | 'translation' | 'set' | 'mixed';
export type ModerationStatus = 'pending' | 'approved' | 'rejected';
export type ComplaintReason =
  | 'wrong_language'
  | 'incorrect_translation'
  | 'inappropriate'
  | 'spam'
  | 'duplicate'
  | 'other';

export interface QualityMetricsSummary {
  learner_count: number;
  sample_size: number;
  global_success_rate: number;
  avg_interval: number;
}

export interface PendingModerationEntry {
  id: number;
  created_at: string;
  updated_at: string | null;
  target_type: ModerationTargetType;
  target_id: number;
  creator_id: number;
  status: ModerationStatus;
  feedback: string | null;
  patch_data: Record<string, unknown>;
  resolved_at: string | null;
  moderator_id: number | null;
  resolution_feedback: string | null;
  quality_metrics: QualityMetricsSummary | null;
  complaint_count: number;
}

export interface ModerationListParams {
  target_type?: ModerationTargetType;
  status?: ModerationStatus;
  skip?: number;
  limit?: number;
}

export interface PromotionCandidateItem {
  id: number;
  term: string;
  language_id: number;
  context: string | null;
  difficulty: number | null;
  part_of_speech: string | null;
  status: string;
  creator_id: number | null;
}

export interface ComplaintRequest {
  reason: ComplaintReason;
  details?: string;
}

export interface ComplaintResponse {
  id: number;
  target_type: ModerationTargetType;
  target_id: number;
  reporter_id: number;
  reason: ComplaintReason;
  details: string | null;
  created_at: string;
}

export interface AdminOverviewStats {
  community_count: number;
  pending_queue_count: number;
  total_complaints: number;
}

export interface AuditLogEntry {
  id: number;
  created_at: string;
  table_name: string;
  record_id: number;
  action: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  user_id: number | null;
}
