import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Volume2, ChevronRight } from 'lucide-react';
import { usePracticeStore } from '../store/practice.store';
import type { AnswerLifecycle } from '../types/practice.types';

const MOTIVATIONAL_MESSAGES = [
  'Writing words in context builds durable memory faster than flashcards.',
  'Every recall strengthens the neural pathway. You\'re building real retention.',
  'Active retrieval is the most powerful memory technique known to science.',
  'Mistakes are the fuel for long-term memory. Keep going.',
];

function getMotivationalMessage(sessionId: number): string {
  return MOTIVATIONAL_MESSAGES[sessionId % MOTIVATIONAL_MESSAGES.length];
}

function wordColor(lifecycle: AnswerLifecycle, isCorrect: boolean): string {
  if (lifecycle === 'correct') return 'text-foreground';
  if (lifecycle === 'corrected') return 'text-amber-600';
  // 'retrying' (abandoned mid-retype) or is_correct=false
  if (!isCorrect) return 'text-red-500';
  return 'text-foreground';
}

export function SessionSummaryView() {
  const navigate = useNavigate();
  const store = usePracticeStore();
  const { summary, items, answers, reset } = store;

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Enter') handleContinue();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  // handleContinue is stable (no deps change), inline deps would cause loop
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.setId, store.practiceAllMode, store.sourceLangId]);

  function handlePlayAudio(url: string) {
    try {
      new Audio(url).play().catch(() => {});
    } catch { /* ignore */ }
  }

  function handleContinue() {
    const { setId, practiceAllMode, sourceLangId } = store;
    reset();
    if (practiceAllMode && sourceLangId) {
      navigate(`/practice?all=true&lang=${sourceLangId}`, { replace: true });
    } else if (setId) {
      navigate(`/practice?setId=${setId}`, { replace: true });
    } else {
      navigate('/sets');
    }
  }

  function handleExit() {
    reset();
    navigate('/dashboard');
  }

  function handlePracticeMistakes() {
    reset();
    navigate('/sets');
  }

  const newWordsCount = items.filter((i) => i.last_reviewed === null).length;
  const correctedCount = Object.values(answers).filter(
    (a) => a.lifecycle === 'corrected',
  ).length;
  const hasMistakes = (summary?.leech_item_ids.length ?? 0) > 0;
  const accuracyPct = summary ? Math.round(summary.accuracy * 100) : 0;

  return (
    <div className="relative flex flex-col items-center px-6 py-12 gap-8 min-h-[calc(100vh-3rem)]">
      {/* Accuracy headline */}
      <div className="flex flex-col items-center gap-1 text-center">
        <h1 className="text-4xl font-bold">{accuracyPct}% accuracy</h1>
        <p className="text-sm text-muted-foreground">
          {summary?.total_reviewed ?? 0} reviewed
          {newWordsCount > 0 && ` · ${newWordsCount} new`}
          {correctedCount > 0 && ` · ${correctedCount} corrected after retry`}
        </p>
      </div>

      {/* Word list */}
      {items.length > 0 && (
        <div className="w-full max-w-2xl">
          <div className="columns-1 sm:columns-2 lg:columns-3 gap-x-6 gap-y-2">
            {items.map((item) => {
              const answer = answers[item.item_id];
              const lifecycle: AnswerLifecycle = answer?.lifecycle ?? 'retrying';
              const isCorrect = answer?.isCorrect ?? false;
              const translation = item.prompt || item.synonyms.slice(0, 3).join(', ');
              const color = wordColor(lifecycle, isCorrect);

              return (
                <div key={item.item_id} className="flex items-baseline gap-2 py-1 break-inside-avoid">
                  {item.audio_url && (
                    <button
                      onClick={() => handlePlayAudio(item.audio_url!)}
                      className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"
                      aria-label={`Play ${item.answer}`}
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <span className={`font-semibold ${color}`}>{item.answer}</span>
                  <span className="text-muted-foreground text-sm shrink-0">—</span>
                  <span className="text-sm text-muted-foreground truncate">{translation}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Motivational message */}
      {summary && (
        <div className="flex flex-col items-center gap-3 text-center max-w-xs">
          <div className="flex items-center gap-3 w-full">
            <span className="flex-1 h-px bg-border" />
            <span className="text-lg">📖</span>
            <span className="flex-1 h-px bg-border" />
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {getMotivationalMessage(summary.session_id)}
          </p>
        </div>
      )}

      {/* Bottom actions */}
      <div className="absolute bottom-6 left-6 right-6 flex items-end justify-between">
        <div className="flex flex-col gap-2">
          {hasMistakes && (
            <button
              onClick={handlePracticeMistakes}
              className="text-sm text-primary hover:underline text-left"
            >
              Practice mistakes →
            </button>
          )}
          <button
            onClick={handleExit}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors text-left"
          >
            Exit
          </button>
        </div>
        <button
          onClick={handleContinue}
          className="flex items-center justify-center w-12 h-12 rounded-full bg-foreground text-background shadow-md hover:opacity-80 active:scale-95 transition-all"
          aria-label="Continue practicing"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
