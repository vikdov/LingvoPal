import { type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/sonner';
import { UnauthorizedError } from '@/services/api';
import { useAuthStore } from '@/features/auth/store/auth.store';

// One QueryClient for the whole app. Created outside the component so it
// survives re-renders and isn't recreated on every mount.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 min — avoids refetching on every focus
      retry: (failureCount, error) => {
        // Never retry auth failures — the token is gone, retrying is pointless.
        if (error instanceof UnauthorizedError) return false;
        return failureCount < 2;
      },
    },
    mutations: {
      onError: (error) => {
        if (error instanceof UnauthorizedError) {
          // Token expired mid-session. Clear state; the router guard will
          // redirect to /auth/login on the next render.
          useAuthStore.getState().clearAuth();
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
  }
};

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
