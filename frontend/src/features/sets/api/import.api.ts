import { api } from '@/services/api';
import type { AnkiConfirmRequest, AnkiImportResponse, AnkiPreviewResponse, LpsetImportResponse } from '../types/import.types';

export const importApi = {
  previewAnki: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.postForm<AnkiPreviewResponse>('/import/anki/preview', form);
  },

  confirmAnki: (body: AnkiConfirmRequest) =>
    api.post<AnkiImportResponse>('/import/anki/confirm', body),

  importLpset: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.postForm<LpsetImportResponse>('/import/lpset', form);
  },
};
