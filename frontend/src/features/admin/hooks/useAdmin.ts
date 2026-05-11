import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../api/admin.api';
import type { ModerationListParams, ModerationTargetType } from '../types/admin.types';

export const adminKeys = {
  all: ['admin'] as const,
  overview: ['admin', 'overview'] as const,
  moderation: (params: ModerationListParams) => ['admin', 'moderation', params] as const,
  promotionCandidates: ['admin', 'promotion-candidates'] as const,
  complaints: (params: object) => ['admin', 'complaints', params] as const,
  auditLog: (params: object) => ['admin', 'audit-log', params] as const,
};

export function useAdminOverview() {
  return useQuery({
    queryKey: adminKeys.overview,
    queryFn: () => adminApi.getOverview(),
    staleTime: 30_000,
  });
}

export function useModerationQueue(params: ModerationListParams = {}) {
  return useQuery({
    queryKey: adminKeys.moderation(params),
    queryFn: () => adminApi.listModeration(params),
  });
}

export function usePromotionCandidates() {
  return useQuery({
    queryKey: adminKeys.promotionCandidates,
    queryFn: () => adminApi.listPromotionCandidates(),
  });
}

export function useAdminComplaints(params: { target_type?: ModerationTargetType; skip?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: adminKeys.complaints(params),
    queryFn: () => adminApi.listComplaints(params),
  });
}

export function useAuditLog(params: { table_name?: string; action?: string; skip?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: adminKeys.auditLog(params),
    queryFn: () => adminApi.listAuditLog(params),
  });
}

export function useApprove() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, feedback }: { id: number; feedback?: string }) =>
      adminApi.approve(id, feedback),
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.all }),
  });
}

export function useReject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, feedback }: { id: number; feedback: string }) =>
      adminApi.reject(id, feedback),
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.all }),
  });
}

export function usePromoteToOfficial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, override }: { itemId: number; override?: boolean }) =>
      adminApi.promoteToOfficial(itemId, override),
    onSuccess: () => qc.invalidateQueries({ queryKey: adminKeys.all }),
  });
}
