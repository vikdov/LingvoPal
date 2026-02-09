// Re-export key symbols for easy import
export * from './api/auth.api';  // Wildcard: Exports everything from auth.api.ts
export { default as AuthForm } from './components/AuthForm';  // Named default export
export { useAuth } from './hooks/useAuth';  // Specific named export
export * from './model/auth.store';  // For stores
export * from './types/auth.types';  // Types for type safety
export { LoginView, RegisterView } from './views';  // Grouped from subfolder

// Optionally, define package-level constants or utilities if needed
export const AUTH_VERSION = '1.0';  // Rare, but for feature-wide config
