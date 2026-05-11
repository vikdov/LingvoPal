import { api } from '@/services/api';
import type { PaginatedResponse } from '@/types/common.types';
import type {
  PendingModerationEntry,
  ModerationListParams,
  PromotionCandidateItem,
  AdminOverviewStats,
  ComplaintResponse,
  AuditLogEntry,
  ModerationTargetType,
} from '../types/admin.types';

export const adminApi = {
  getOverview: (): Promise<AdminOverviewStats> =>
    api.get('/admin/overview'),

  listModeration: (params: ModerationListParams = {}): Promise<PaginatedResponse<PendingModerationEntry>> => {
    const qs = new URLSearchParams();
    if (params.target_type) qs.set('target_type', params.target_type);
    if (params.status)      qs.set('status',      params.status);
    if (params.skip != null) qs.set('skip',        String(params.skip));
    if (params.limit != null) qs.set('limit',      String(params.limit));
    const query = qs.toString();
    return api.get(`/admin/moderation${query ? `?${query}` : ''}`);
  },

  getModeration: (id: number): Promise<PendingModerationEntry> =>
    api.get(`/admin/moderation/${id}`),

  approve: (id: number, resolution_feedback?: string): Promise<PendingModerationEntry> =>
    api.post(`/admin/moderation/${id}/approve`, { resolution_feedback }),

  reject: (id: number, resolution_feedback: string): Promise<PendingModerationEntry> =>
    api.post(`/admin/moderation/${id}/reject`, { resolution_feedback }),

  listPromotionCandidates: (skip = 0, limit = 20): Promise<PromotionCandidateItem[]> =>
    api.get(`/admin/items/promotion-candidates?skip=${skip}&limit=${limit}`),

  promoteToOfficial: (itemId: number, override = false): Promise<PromotionCandidateItem> =>
    api.post(`/admin/items/${itemId}/promote`, { override }),

  listComplaints: (params: { target_type?: ModerationTargetType; skip?: number; limit?: number } = {}): Promise<PaginatedResponse<ComplaintResponse>> => {
    const qs = new URLSearchParams();
    if (params.target_type) qs.set('target_type', params.target_type);
    if (params.skip != null) qs.set('skip', String(params.skip));
    if (params.limit != null) qs.set('limit', String(params.limit));
    return api.get(`/admin/complaints?${qs}`);
  },

  listAuditLog: (params: { table_name?: string; action?: string; skip?: number; limit?: number } = {}): Promise<PaginatedResponse<AuditLogEntry>> => {
    const qs = new URLSearchParams();
    if (params.table_name) qs.set('table_name', params.table_name);
    if (params.action)     qs.set('action', params.action);
    if (params.skip != null) qs.set('skip', String(params.skip));
    if (params.limit != null) qs.set('limit', String(params.limit));
    return api.get(`/admin/audit-log?${qs}`);
  },
};
