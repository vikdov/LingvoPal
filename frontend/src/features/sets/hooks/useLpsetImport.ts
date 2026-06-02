import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { importApi } from '../api/import.api';

export function useLpsetImport() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: (file: File) => importApi.importLpset(file),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['sets', 'created'] });
      qc.invalidateQueries({ queryKey: ['sets', 'library'] });
      navigate(`/sets/${data.set_id}`);
    },
  });
}
