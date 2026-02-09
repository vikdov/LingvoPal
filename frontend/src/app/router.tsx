import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';

// 1. Layout Imports
import { AppLayout } from '@/components/layout/AppLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { PublicLayout } from '@/components/layout/PublicLayout';

// 2. Feature View Imports (Importing from the feature's public API)
import { LandingView } from '@/features/landing';
import { LoginView, RegisterView } from '@/features/auth';
import { DashboardView } from '@/features/stats';
import { SetsListView, SetDetailView } from '@/features/sets';
import { PracticeView, SessionSummaryView } from '@/features/practice';
import { SettingsView } from '@/features/settings';

// 3. App-Level Imports
import { NotFoundView } from './NotFoundView';
import { useAuthStore } from '@/features/auth/model/auth.store'; // Direct store access for the guard

/**
 * GUARD: Protected Route Wrapper
 * Checks if the user is authenticated. 
 * If yes, renders the child route (Outlet).
 * If no, redirects to login.
 */
const ProtectedRoute = () => {
  // We use the selector pattern to avoid unnecessary re-renders
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }

  return <Outlet />;
};

/**
 * GUARD: Public Route Wrapper (Optional)
 * Prevents logged-in users from seeing the Landing/Login page 
 * and sends them straight to the dashboard.
 */
const PublicOnlyRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
};

export const router = createBrowserRouter([
  // --- PUBLIC ROUTES (Landing, Marketing) ---
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        path: '/',
        element: <PublicLayout />,
        children: [
          { index: true, element: <LandingView /> },
        ],
      },
      // --- AUTH ROUTES (Login, Register) ---
      {
        path: 'auth',
        element: <AuthLayout />,
        children: [
          { path: 'login', element: <LoginView /> },
          { path: 'register', element: <RegisterView /> },
        ],
      },
    ],
  },

  // --- PROTECTED APP ROUTES (Dashboard, Practice, etc.) ---
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />, // The Sidebar + Header shell
        children: [
          // Dashboard
          { path: 'dashboard', element: <DashboardView /> },

          // Sets (Library)
          { path: 'sets', element: <SetsListView /> },
          { path: 'sets/:setId', element: <SetDetailView /> },

          // Practice Mode
          { path: 'practice', element: <PracticeView /> },
          { path: 'practice/summary', element: <SessionSummaryView /> },

          // Settings
          { path: 'settings', element: <SettingsView /> },
        ],
      },
    ],
  },

  // --- 404 CATCH-ALL ---
  {
    path: '*',
    element: <NotFoundView />,
  },
]);
