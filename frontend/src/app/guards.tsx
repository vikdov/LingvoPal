import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/store/auth.store';
import { useInterfaceLanguage } from '@/features/settings/hooks/useSettings';

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
  const user = useAuthStore((state) => state.user);
  if (!user?.is_admin) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
