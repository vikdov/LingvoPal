import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { createElement } from 'react';
import { AdminDashboard } from '../AdminDashboard';

vi.mock('../../api/admin.api', () => ({
  adminApi: {
    listModeration: vi.fn(),
    getModeration: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
  },
}));

import { adminApi } from '../../api/admin.api';

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    createElement(QueryClientProvider, { client: qc },
      createElement(MemoryRouter, null, ui)
    )
  );
}

beforeEach(() => vi.clearAllMocks());

describe('AdminDashboard', () => {
  it('renders heading', () => {
    vi.mocked(adminApi.listModeration).mockResolvedValue({ data: [], total: 0, page: 1, page_size: 1, pages: 0, has_next: false, has_prev: false });
    renderWithProviders(createElement(AdminDashboard));
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('renders StatCard labels', () => {
    vi.mocked(adminApi.listModeration).mockResolvedValue({ data: [], total: 0, page: 1, page_size: 1, pages: 0, has_next: false, has_prev: false });
    renderWithProviders(createElement(AdminDashboard));
    expect(screen.getByText('Pending items')).toBeInTheDocument();
    expect(screen.getByText('Pending sets')).toBeInTheDocument();
  });

  it('StatCard shows count when data loads', async () => {
    vi.mocked(adminApi.listModeration).mockResolvedValue({ data: [], total: 7, page: 1, page_size: 1, pages: 7, has_next: true, has_prev: false });
    renderWithProviders(createElement(AdminDashboard));
    const counts = await screen.findAllByText('7');
    expect(counts.length).toBeGreaterThanOrEqual(1);
  });

  it('StatCard links to correct routes', () => {
    vi.mocked(adminApi.listModeration).mockResolvedValue({ data: [], total: 0, page: 1, page_size: 1, pages: 0, has_next: false, has_prev: false });
    renderWithProviders(createElement(AdminDashboard));
    expect(screen.getByText('Pending items').closest('a')).toHaveAttribute('href', '/admin/items');
    expect(screen.getByText('Pending sets').closest('a')).toHaveAttribute('href', '/admin/sets');
  });

  it('shows content lifecycle note', () => {
    vi.mocked(adminApi.listModeration).mockResolvedValue({ data: [], total: 0, page: 1, page_size: 1, pages: 0, has_next: false, has_prev: false });
    renderWithProviders(createElement(AdminDashboard));
    expect(screen.getByText(/DRAFT → PENDING_REVIEW → APPROVED/)).toBeInTheDocument();
  });
});
