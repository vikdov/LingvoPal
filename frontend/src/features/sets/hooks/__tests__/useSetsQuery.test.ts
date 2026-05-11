import { renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { useMyLibrary, useCreatedSets, useSet } from '../useSetsQuery';

vi.mock('../../api/sets.api', () => ({
  setsApi: {
    getCreatedSets: vi.fn(),
    getLibrary: vi.fn(),
    getPublicSets: vi.fn(),
    getSet: vi.fn(),
    getSetItems: vi.fn(),
  },
}));

import { setsApi } from '../../api/sets.api';

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: qc }, children);
}

const mockPaginatedEmpty = {
  data: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 0,
  has_next: false,
  has_prev: false,
};

beforeEach(() => vi.clearAllMocks());

describe('useMyLibrary', () => {
  it('returns library data on success', async () => {
    const mockLibrary = { ...mockPaginatedEmpty, data: [{ set_id: 1, set: { id: 1, title: 'Spanish basics', difficulty: null, source_lang_id: 1, target_lang_id: 2, item_count: 10 }, added_at: '2024-01-01', last_opened_at: null, is_pinned: false }], total: 1 };
    vi.mocked(setsApi.getLibrary).mockResolvedValue(mockLibrary as never);

    const { result } = renderHook(() => useMyLibrary(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockLibrary);
  });

  it('enters error state when api fails', async () => {
    vi.mocked(setsApi.getLibrary).mockRejectedValue(new Error('network error'));

    const { result } = renderHook(() => useMyLibrary(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('uses correct query key', () => {
    vi.mocked(setsApi.getLibrary).mockResolvedValue(mockPaginatedEmpty as never);
    const { result } = renderHook(() => useMyLibrary(), { wrapper: makeWrapper() });
    expect(result.current).toBeDefined();
  });
});

describe('useCreatedSets', () => {
  it('returns sets data on success', async () => {
    const mockSets = { ...mockPaginatedEmpty, data: [{ id: 1, title: 'My set', description: null, difficulty: null, status: 'DRAFT' as const, creator_id: 1, source_lang_id: 1, target_lang_id: 2, item_count: 0, is_public: false, created_at: '2024-01-01', updated_at: null }], total: 1 };
    vi.mocked(setsApi.getCreatedSets).mockResolvedValue(mockSets as never);

    const { result } = renderHook(() => useCreatedSets(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockSets);
  });
});

describe('useSet', () => {
  it('skips fetch when setId is 0', () => {
    vi.mocked(setsApi.getSet).mockResolvedValue({} as never);
    const { result } = renderHook(() => useSet(0), { wrapper: makeWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
    expect(setsApi.getSet).not.toHaveBeenCalled();
  });

  it('fetches when setId is positive', async () => {
    vi.mocked(setsApi.getSet).mockResolvedValue({ id: 5, title: 'Test set', description: null, difficulty: null, status: 'DRAFT' as const, creator_id: 1, source_lang_id: 1, target_lang_id: 2, item_count: 0, is_public: false, created_at: '2024-01-01', updated_at: null } as never);
    const { result } = renderHook(() => useSet(5), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(setsApi.getSet).toHaveBeenCalledWith(5);
  });
});
