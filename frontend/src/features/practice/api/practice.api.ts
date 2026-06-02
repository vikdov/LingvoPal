import { api } from '@/services/api';
import type {
  ActiveSession,
  SessionStarted,
  SubmitAnswerRequest,
  AnswerBufferedResponse,
  SessionSummary,
} from '../types/practice.types';

export const practiceApi = {
  getActiveSession: () =>
    api.get<ActiveSession>('/practice/sessions/active'),

  startSession: (params: { set_id: number; force?: boolean } | { practice_all: true; source_lang_id: number; force?: boolean }) =>
    api.post<SessionStarted>('/practice/sessions', params),

  submitAnswer: (sessionId: number, body: SubmitAnswerRequest) =>
    api.post<AnswerBufferedResponse>(`/practice/sessions/${sessionId}/answers`, body),

  finalise: (sessionId: number) =>
    api.post<SessionSummary>(`/practice/sessions/${sessionId}/finalise`),

  abandon: (sessionId: number) =>
    api.post<SessionSummary>(`/practice/sessions/${sessionId}/abandon`),

  getSummary: (sessionId: number) =>
    api.get<SessionSummary>(`/practice/sessions/${sessionId}/summary`),
};
