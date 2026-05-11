import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { importApi } from '../api/import.api';
import type { AnkiConfirmRequest } from '../types/import.types';

export function useAnkiPreview() {
  return useMutation({
    mutationFn: (file: File) => importApi.previewAnki(file),
  });
}

export function useAnkiConfirm() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (body: AnkiConfirmRequest) => importApi.confirmAnki(body),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
      navigate(`/sets/${data.set_id}`);
    },
  });
}
