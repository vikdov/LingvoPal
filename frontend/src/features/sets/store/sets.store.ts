import { create } from 'zustand';

// Only genuinely cross-render UI state lives here.
// Per-component state (modal open, form values) stays in useState.
interface SetsUIState {
  activeTab: 'mine' | 'discover';
  setActiveTab: (tab: 'mine' | 'discover') => void;
}

export const useSetsStore = create<SetsUIState>()((set) => ({
  activeTab: 'mine',
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
