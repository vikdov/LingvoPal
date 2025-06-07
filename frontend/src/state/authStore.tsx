// frontend/src/store/authStore.js
import { create } from 'zustand';
import { createClient } from '@supabase/supabase-js';
import type { User } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

interface SignupData {
  name: string;
  email: string;
  password: string;
  nativeLanguage: string;
  learningLanguage: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  fetchUser: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (data: SignupData) => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,
  error: null,
  fetchUser: async () => {
    set({ loading: true, error: null });
    try {
      const { data: { user } } = await supabase.auth.getUser();
      set({ user, loading: false });
    } catch (error) {
      set({ error: 'Failed to fetch user', loading: false });
    }
  },
  signIn: async (email: string, password: string) => {
    set({ loading: true, error: null });
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
      set({ user: data.user, loading: false });
    } catch (error) {
      set({ error: 'Failed to sign in', loading: false });
    }
  },
  signUp: async (data: SignupData) => {
    set({ loading: true, error: null });
    try {
      // First, create the auth user
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
      });
      if (authError) throw authError;

      // Then, create the user profile in the profiles table
      const { error: profileError } = await supabase
        .from('profiles')
        .insert([
          {
            id: authData.user?.id,
            name: data.name,
            native_language: data.nativeLanguage,
            learning_language: data.learningLanguage,
          },
        ]);

      if (profileError) throw profileError;
      set({ user: authData.user, loading: false });
    } catch (error) {
      set({ error: 'Failed to sign up', loading: false });
      throw error;
    }
  },
  signOut: async () => {
    set({ loading: true, error: null });
    try {
      await supabase.auth.signOut();
      set({ user: null, loading: false });
    } catch (error) {
      set({ error: 'Failed to sign out', loading: false });
    }
  },
}));