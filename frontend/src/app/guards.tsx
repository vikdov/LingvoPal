import { Navigate, Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/features/auth/store/auth.store';
import { useInterfaceLanguage } from '@/features/settings/hooks/useSettings';
import { settingsApi } from '@/features/settings/api/settings.api';
import { Spinner } from '@/components/ui/spinner';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  useInterfaceLanguage();
  if (!isAuthenticated) return <Navigate to="/auth/login" replace />;
  return <Outlet />;
}

export function PublicOnlyRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

export function AdminRoute() {
  // Re-fetch the live user profile to validate role — the cached store value
  // may be stale if admin privileges were revoked since last login.
  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile', 'me'],
    queryFn: settingsApi.getProfile,
    staleTime: 60_000,
  });

  if (isLoading) return <div className="flex h-screen items-center justify-center"><Spinner className="size-6" /></div>;
  if (!profile?.is_admin) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
