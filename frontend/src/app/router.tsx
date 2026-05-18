import { createBrowserRouter } from 'react-router-dom';

// 1. Layout Imports
import { AppLayout } from '@/components/layout/AppLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { LandingLayout } from '@/components/layout/LandingLayout';
import { PracticeLayout } from '@/components/layout/PracticeLayout';

// 2. Feature View Imports (Importing from the feature's public API)
import { LandingView } from '@/features/landing';
import {
  LoginView,
  RegisterView,
  VerifyEmailView,
  ForgotPasswordView,
  ResetPasswordView,
  EmailChangeConfirmView,
} from '@/features/auth';
import { DashboardView } from '@/features/stats';
import { SetsListView, SetDetailView, SetDiscoveryView, ItemDiscoveryView, ExpressionsLibraryView } from '@/features/sets';
import { PracticeView, SessionSummaryView } from '@/features/practice';
import { SettingsView } from '@/features/settings';
import { AdminDashboard } from '@/features/admin';

// 3. App-Level Imports
import { NotFoundView } from './NotFoundView';
import { ProtectedRoute, PublicOnlyRoute, AdminRoute } from './guards';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export const router = createBrowserRouter([
  // --- PUBLIC ROUTES (Landing, Marketing) ---
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        path: '/',
        element: <LandingLayout />,
        children: [
          { index: true, element: <LandingView /> },
        ],
      },
      // --- AUTH ROUTES (Login, Register — redirect to app if already logged in) ---
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

  // --- OPEN AUTH ROUTES (accessible regardless of auth state) ---
  // These must not be inside PublicOnlyRoute so logged-in users can still use them
  // (e.g., clicking a reset/verify link from email while already logged in).
  {
    path: 'auth',
    element: <AuthLayout />,
    children: [
      { path: 'forgot-password', element: <ForgotPasswordView /> },
      { path: 'reset-password', element: <ResetPasswordView /> },
      { path: 'change-email', element: <EmailChangeConfirmView /> },
    ],
  },
  {
    path: 'verify',
    element: <AuthLayout />,
    children: [{ index: true, element: <VerifyEmailView /> }],
  },

  // --- PROTECTED APP ROUTES (Dashboard, Practice, etc.) ---
  {
    element: <ProtectedRoute />,
    children: [
      // Practice — full-screen, no sidebar
      {
        element: <ErrorBoundary><PracticeLayout /></ErrorBoundary>,
        children: [
          { path: 'practice', element: <PracticeView /> },
          { path: 'practice/summary', element: <SessionSummaryView /> },
        ],
      },

      // Everything else — sidebar + header shell
      {
        element: <ErrorBoundary><AppLayout /></ErrorBoundary>,
        children: [
          // Dashboard
          { path: 'dashboard', element: <DashboardView /> },

          // Sets (Library)
          { path: 'sets', element: <SetsListView /> },
          { path: 'sets/discover', element: <SetDiscoveryView /> },
          { path: 'items/discover', element: <ItemDiscoveryView /> },
          { path: 'sets/:setId', element: <SetDetailView /> },
          { path: 'words', element: <ExpressionsLibraryView /> },

          // Settings
          { path: 'settings', element: <SettingsView /> },

          // Admin (role check enforced at backend + frontend guard)
          {
            element: <AdminRoute />,
            children: [
              { path: 'admin', element: <AdminDashboard /> },
            ],
          },
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
