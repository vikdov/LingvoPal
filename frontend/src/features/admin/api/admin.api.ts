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
  OfficialSetEntry,
  ImportSetResult,
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

  dismissComplaint: (id: number): Promise<void> =>
    api.delete(`/admin/complaints/${id}`),

  deleteItem: (id: number, reason: string): Promise<void> =>
    api.delete(`/admin/items/${id}?${new URLSearchParams({ reason })}`),

  deleteSet: (id: number, reason: string): Promise<void> =>
    api.delete(`/admin/sets/${id}?${new URLSearchParams({ reason })}`),

  listAuditLog: (params: { table_name?: string; action?: string; skip?: number; limit?: number } = {}): Promise<PaginatedResponse<AuditLogEntry>> => {
    const qs = new URLSearchParams();
    if (params.table_name) qs.set('table_name', params.table_name);
    if (params.action)     qs.set('action', params.action);
    if (params.skip != null) qs.set('skip', String(params.skip));
    if (params.limit != null) qs.set('limit', String(params.limit));
    return api.get(`/admin/audit-log?${qs}`);
  },

  listOfficialSets: (): Promise<OfficialSetEntry[]> =>
    api.get('/admin/sets/official'),

  importOfficialSet: (file: File): Promise<ImportSetResult> => {
    const form = new FormData();
    form.append('file', file);
    return api.postForm('/admin/sets/import', form);
  },

  exportSet: async (setId: number, title: string): Promise<void> => {
    const blob = await api.getBlob(`/sets/${setId}/export`);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.lpset`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
