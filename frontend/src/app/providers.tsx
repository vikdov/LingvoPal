import { type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import { ApiError, UnauthorizedError } from '@/services/api';
import { useAuthStore } from '@/features/auth/store/auth.store';
import i18n from '@/i18n/config';

// One QueryClient for the whole app. Created outside the component so it
// survives re-renders and isn't recreated on every mount.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 min — avoids refetching on every focus
      retry: (failureCount, error) => {
        // Don't retry auth failures or any client errors (4xx).
        if (error instanceof ApiError && error.status < 500) return false;
        return failureCount < 2;
      },
    },
    mutations: {
      onError: (error) => {
        if (error instanceof UnauthorizedError) {
          useAuthStore.getState().clearAuth();
        } else if (error instanceof ApiError && error.status === 429) {
          toast.error(i18n.t('common.tooManyRequests'));
        }
      },
    },
  },
});

// Wire a global query error handler separately so we can call it after the
// client is constructed (avoids a chicken-and-egg reference).
queryClient.getQueryCache().config.onError = (error) => {
  if (error instanceof UnauthorizedError) {
    useAuthStore.getState().clearAuth();
  } else if (error instanceof ApiError && error.status === 429) {
    toast.error(i18n.t('common.tooManyRequests'));
  }
};

// NOTE: BootRefresh was removed. It called authApi.refresh() via rawPost,
// which bypassed the _refreshPromise dedup lock in api.ts. On page reload,
// both BootRefresh and the first 401-triggered auto-retry in api.ts would
// fire concurrently, consuming the rotated refresh token twice — silently
// logging the user out. The auto-retry in api.ts handles the silent refresh
// correctly and is sufficient on its own.

interface Props {
  children: ReactNode;
}

export function Providers({ children }: Props) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  );
}
