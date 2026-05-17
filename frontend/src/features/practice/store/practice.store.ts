import { create } from 'zustand';
import { ApiError } from '@/services/api';
import { practiceApi } from '../api/practice.api';
import { evaluateAnswer } from '../utils/answerMatcher';
import type {
  ItemHint,
  ComparisonConfig,
  AnswerRecord,
  AnswerLifecycle,
  SessionSummary,
  SessionPhase,
  SubmitAnswerRequest,
} from '../types/practice.types';

const DEFAULT_CONFIG: ComparisonConfig = {
  evaluation_mode: 'normal',
  show_hints_on_fails: true,
  show_translations: true,
  show_images: true,
  show_synonyms: true,
  show_part_of_speech: true,
  auto_play_audio: false,
};

// ── Persistence helpers ───────────────────────────────────────────────────────

const SESSION_KEY = 'lingvopal_practice_session';
const CONFIG_KEY  = 'lingvopal_practice_config';

function loadUserConfig(): Partial<ComparisonConfig> {
  try {
    const raw = localStorage.getItem(CONFIG_KEY);
    return raw ? (JSON.parse(raw) as Partial<ComparisonConfig>) : {};
  } catch { return {}; }
}

function saveUserConfig(config: ComparisonConfig) {
  try { localStorage.setItem(CONFIG_KEY, JSON.stringify(config)); } catch { /* ignore */ }
}

type PersistedSession = Pick<
  PracticeState,
  'sessionId' | 'setId' | 'practiceAllMode' | 'sourceLangId' | 'items' | 'config' | 'currentIndex' | 'answers' | 'phase'
>;

function loadSession(): Partial<PracticeState> | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedSession;
    if (parsed.phase !== 'active') return null;
    return { ...parsed, itemStartedAt: Date.now(), pendingPayload: null, summary: null, error: null, nextReviewAt: null };
  } catch { return null; }
}

function saveSession(state: PracticeState) {
  try {
    if (state.phase !== 'active') { sessionStorage.removeItem(SESSION_KEY); return; }
    const { sessionId, setId, practiceAllMode, sourceLangId, items, config, currentIndex, answers, phase } = state;
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ sessionId, setId, practiceAllMode, sourceLangId, items, config, currentIndex, answers, phase }));
  } catch { /* ignore quota errors */ }
}


interface PendingPayload {
  sessionId: number;
  body: SubmitAnswerRequest;
}

interface PracticeState {
  sessionId:       number | null;
  setId:           number | null;
  practiceAllMode: boolean;
  sourceLangId:    number | null;
  items:           ItemHint[];
  config:          ComparisonConfig;
  currentIndex:    number;
  answers:         Record<number, AnswerRecord>;
  phase:           SessionPhase;
  summary:         SessionSummary | null;
  error:           string | null;
  nextReviewAt:    string | null;
  itemStartedAt:   number | null;
  pendingPayload:  PendingPayload | null;

  startSession:          (setId: number, force?: boolean) => Promise<void>;
  startSessionAll:       (sourceLangId: number, force?: boolean) => Promise<void>;
  submitAnswer:          (userAnswer: string) => void;
  setConfidenceOverride: (itemId: number, override: number | null) => void;
  resolveRetype:         (itemId: number) => void;
  nextItem:              () => void;
  finalise:              () => Promise<void>;
  abandon:               () => Promise<void>;
  reset:                 () => void;
  updateConfig:          (patch: Partial<ComparisonConfig>) => void;
}

const RESET_STATE = {
  sessionId: null, setId: null, practiceAllMode: false, sourceLangId: null,
  items: [], config: DEFAULT_CONFIG, currentIndex: 0, answers: {},
  phase: 'idle' as SessionPhase, summary: null, error: null, nextReviewAt: null,
  itemStartedAt: null, pendingPayload: null,
};

const _initialState = (() => {
  const restored = loadSession();
  return restored ? { ...RESET_STATE, ...restored } : RESET_STATE;
})();

export const usePracticeStore = create<PracticeState>()((set, get) => ({
  ..._initialState,

  startSession: async (setId, force = false) => {
    set({ phase: 'loading', error: null, nextReviewAt: null, setId, practiceAllMode: false, sourceLangId: null });
    try {
      const data = await practiceApi.startSession({ set_id: setId, force });
      set({
        sessionId:    data.session_id,
        items:        data.items,
        config:       { ...data.comparison_config, ...loadUserConfig() },
        currentIndex: data.current_index,
        answers:      {},
        phase:        'active',
        summary:      null,
        itemStartedAt: Date.now(),
      });
    } catch (err) {
      if (err instanceof ApiError && err.code === 'no_due_items') {
        const nextReviewAt = typeof err.extra.next_review_at === 'string' ? err.extra.next_review_at : null;
        set({ phase: 'no_due_items', nextReviewAt });
        return;
      }
      set({ phase: 'error', error: err instanceof Error ? err.message : 'Failed to start session.' });
    }
  },

  startSessionAll: async (sourceLangId, force = false) => {
    set({ phase: 'loading', error: null, nextReviewAt: null, setId: null, practiceAllMode: true, sourceLangId });
    try {
      const data = await practiceApi.startSession({ practice_all: true, source_lang_id: sourceLangId, force });
      set({
        sessionId:    data.session_id,
        items:        data.items,
        config:       { ...data.comparison_config, ...loadUserConfig() },
        currentIndex: data.current_index,
        answers:      {},
        phase:        'active',
        summary:      null,
        itemStartedAt: Date.now(),
      });
    } catch (err) {
      if (err instanceof ApiError && err.code === 'no_due_items') {
        const nextReviewAt = typeof err.extra.next_review_at === 'string' ? err.extra.next_review_at : null;
        set({ phase: 'no_due_items', nextReviewAt });
        return;
      }
      set({ phase: 'error', error: err instanceof Error ? err.message : 'Failed to start session.' });
    }
  },

  submitAnswer: (userAnswer) => {
    const { sessionId, items, currentIndex, itemStartedAt, config, phase } = get();
    if (!sessionId || phase !== 'active') return;

    const item = items[currentIndex];
    if (!item) return;

    const responseTimeMs = Math.max(100, Math.min(120_000,
      Date.now() - (itemStartedAt ?? Date.now()),
    ));
    const { isCorrect, similarity } = evaluateAnswer(userAnswer, item.answer, config.evaluation_mode);
    const lifecycle: AnswerLifecycle = isCorrect ? 'correct' : 'retrying';

    const record: AnswerRecord = {
      itemId: item.item_id,
      userAnswer,
      isCorrect,
      similarity,
      responseTimeMs,
      lifecycle,
      confidenceOverride: null,
    };

    // Buffer the payload — fired when user navigates next, so confidence_override can be included.
    const payload: PendingPayload = {
      sessionId,
      body: {
        answer_id: crypto.randomUUID(),
        item_id: item.item_id,
        user_answer: userAnswer,
        response_time_ms: responseTimeMs,
      },
    };

    set((s) => ({
      answers: { ...s.answers, [item.item_id]: record },
      pendingPayload: payload,
    }));
  },

  setConfidenceOverride: (itemId, override) => {
    set((s) => {
      const existing = s.answers[itemId];
      if (!existing) return {};
      const pendingPayload = s.pendingPayload
        ? { ...s.pendingPayload, body: { ...s.pendingPayload.body, confidence_override: override ?? undefined } }
        : null;
      return {
        answers: { ...s.answers, [itemId]: { ...existing, confidenceOverride: override } },
        pendingPayload,
      };
    });
  },

  resolveRetype: (itemId) => {
    set((s) => {
      const existing = s.answers[itemId];
      if (!existing) return {};
      return {
        answers: {
          ...s.answers,
          [itemId]: { ...existing, lifecycle: 'corrected' as AnswerLifecycle },
        },
      };
    });
  },

  nextItem: () => {
    const { currentIndex, items, pendingPayload } = get();
    if (pendingPayload) {
      void practiceApi.submitAnswer(pendingPayload.sessionId, pendingPayload.body).catch(() => {});
      set({ pendingPayload: null });
    }
    if (currentIndex < items.length - 1) {
      set({ currentIndex: currentIndex + 1, phase: 'active', itemStartedAt: Date.now() });
    }
  },

  finalise: async () => {
    const { sessionId, pendingPayload } = get();
    if (!sessionId) return;
    if (pendingPayload) {
      void practiceApi.submitAnswer(pendingPayload.sessionId, pendingPayload.body).catch(() => {});
      set({ pendingPayload: null });
    }
    set({ phase: 'finalising' });
    try {
      const summary = await practiceApi.finalise(sessionId);
      set({ summary, phase: 'complete' });
    } catch {
      set({ phase: 'complete' });
    }
  },

  abandon: async () => {
    const { sessionId } = get();
    if (!sessionId) return;
    try {
      const summary = await practiceApi.abandon(sessionId);
      set({ summary, phase: 'complete', sessionId: null });
    } catch {
      set({ phase: 'idle', sessionId: null });
    }
  },

  reset: () => set(RESET_STATE),

  updateConfig: (patch) => {
    set((s) => {
      const updated = { ...s.config, ...patch };
      saveUserConfig(updated);
      return { config: updated };
    });
  },
}));

usePracticeStore.subscribe(saveSession);
