import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface LanguageState {
  activeLanguageId: number | null;
  setActive: (id: number) => void;
  setActiveFromServer: (id: number) => void;
  clear: () => void;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      activeLanguageId: null,

      setActive: (id) => set({ activeLanguageId: id }),

      // Server is authoritative — always sync on load
      setActiveFromServer: (id) => set({ activeLanguageId: id }),

      clear: () => set({ activeLanguageId: null }),
    }),
    {
      name: 'lp-active-language',
      partialize: (s) => ({ activeLanguageId: s.activeLanguageId }),
    },
  ),
);
