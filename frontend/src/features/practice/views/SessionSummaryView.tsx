import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Volume2, ArrowRightIcon, Flame } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { usePracticeStore } from '../store/practice.store';
import { useOverview, statKeys } from '@/features/stats/hooks/useStats';
import { useLanguageStore } from '@/features/languages/store/language.store';

const MOTIVATIONAL_MESSAGES = [
  'Writing words in context builds durable memory faster than flashcards.',
  'Every recall strengthens the neural pathway. You\'re building real retention.',
  'Active retrieval is the most powerful memory technique known to science.',
  'Mistakes are the fuel for long-term memory. Keep going.',
  'Consistent short sessions beat occasional long ones every time.',
  'Your brain consolidates this vocabulary while you sleep tonight.',
];

function getMotivationalMessage(sessionId: number): string {
  return MOTIVATIONAL_MESSAGES[sessionId % MOTIVATIONAL_MESSAGES.length];
}

function getMilestoneLabel(streak: number): string | null {
  if (streak === 1) return 'First day!';
  if (streak === 3) return '3-day streak';
  if (streak === 7) return '1 week streak';
  if (streak === 14) return '2 week streak';
  if (streak === 30) return '1 month streak';
  if (streak === 100) return '100 days!';
  if (streak > 0 && streak % 50 === 0) return `${streak} days!`;
  return null;
}

function WordChars({ answer, userAnswer }: { answer: string; userAnswer: string }) {
  return (
    <>
      {answer.split('').map((char, i) => {
        const typed = userAnswer?.[i];
        const correct = typed !== undefined && typed.toLowerCase() === char.toLowerCase();
        return (
          <span key={i} className={correct ? 'text-navy' : 'text-orange-500'}>
            {char}
          </span>
        );
      })}
    </>
  );
}

export function SessionSummaryView() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const store = usePracticeStore();
  const { summary, items, answers, reset } = store;
  const { data: overview } = useOverview();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);

  const activeLang = overview?.languages.find((l) => l.language_id === activeLanguageId);
  const streak = activeLang?.streak_days ?? 0;
  const milestoneLabel = getMilestoneLabel(streak);

  useEffect(() => {
    queryClient.invalidateQueries({ queryKey: statKeys.overview() });
    queryClient.invalidateQueries({ queryKey: statKeys.totals() });
    if (store.sourceLangId) {
      queryClient.invalidateQueries({ queryKey: statKeys.vocabMaturity(store.sourceLangId) });
    }
  }, [queryClient, store.sourceLangId]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Enter') handleContinue();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.setId, store.practiceAllMode, store.sourceLangId]);

  function handlePlayAudio(url: string) {
    try { new Audio(url).play().catch(() => {}); } catch { /* ignore */ }
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

  const newWordsCount = items.filter((i) => i.last_reviewed === null).length;
  const correctedCount = Object.values(answers).filter((a) => a.lifecycle === 'corrected').length;
  const accuracyPct = summary ? Math.round(summary.accuracy * 100) : 0;

  return (
    <div className="flex flex-col min-h-screen bg-muted">
      <div className="flex-1 flex flex-col items-center justify-center px-8 py-16 gap-10">

        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-6xl font-bold text-navy">{t('summary.accuracy', { pct: accuracyPct })}</h1>
          <p className="text-base text-navy">
            {newWordsCount > 0 && <><span className="font-bold">{newWordsCount}</span> {t('summary.new')} · </>}
            <span className="font-bold">{summary?.total_reviewed ?? 0}</span> {t('summary.reviewed')}
            {correctedCount > 0 && <> · <span className="font-bold">{correctedCount}</span> {t('summary.corrected')}</>}
          </p>
        </div>

        {streak > 0 && (
          <div className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-1.5 text-orange-500">
              <Flame className="size-5" />
              <span className="text-lg font-bold">{t('summary.dayStreak', { streak })}</span>
            </div>
            {milestoneLabel && (
              <span className="text-xs font-mono text-orange-400 uppercase tracking-widest">
                {milestoneLabel}
              </span>
            )}
          </div>
        )}

        {items.length > 0 && (
          <div className="w-full max-w-5xl">
            <div className="columns-1 sm:columns-2 lg:columns-3 gap-x-12 gap-y-1">
              {items.map((item) => {
                const answer = answers[item.item_id];
                const userAnswer = answer?.userAnswer ?? '';
                const isFullyCorrect = answer?.isCorrect ?? false;
                const translation = item.prompt || item.synonyms.slice(0, 3).join(', ');

                return (
                  <div key={item.item_id} className="flex items-baseline gap-1.5 py-1.5 break-inside-avoid">
                    {item.audio_url ? (
                      <button
                        onClick={() => handlePlayAudio(item.audio_url!)}
                        className="shrink-0 text-navy hover:opacity-70 transition-opacity"
                        aria-label={`Play ${item.answer}`}
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <span className="w-3.5 shrink-0" />
                    )}
                    <span className="font-semibold text-base">
                      {isFullyCorrect
                        ? <span className="text-navy">{item.answer}</span>
                        : <WordChars answer={item.answer} userAnswer={userAnswer} />
                      }
                    </span>
                    <span className="text-navy text-base shrink-0">—</span>
                    <span className="text-base text-navy">{translation}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {summary && (
          <div className="flex flex-col items-center gap-3 text-center max-w-sm">
            <div className="flex items-center gap-3 w-full">
              <span className="flex-1 h-px bg-orange-400" />
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-orange-400">
                <path d="M2 6c0-1.1.9-2 2-2h7a3 3 0 0 1 3 3v13a1.5 1.5 0 0 0-1.5-1.5H4a2 2 0 0 1-2-2V6Z" />
                <path d="M22 6c0-1.1-.9-2-2-2h-7a3 3 0 0 0-3 3v13a1.5 1.5 0 0 1 1.5-1.5H20a2 2 0 0 0 2-2V6Z" />
              </svg>
              <span className="flex-1 h-px bg-orange-400" />
            </div>
            <p className="text-base text-navy leading-relaxed">
              {getMotivationalMessage(summary.session_id)}
            </p>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between px-6 pb-6 pt-2 shrink-0">
        <button
          onClick={handleExit}
          className="text-sm font-semibold text-navy underline underline-offset-2 hover:opacity-60 transition-opacity"
        >
          {t('summary.exit')}
        </button>
        <button
          onClick={handleContinue}
          aria-label={t('summary.continueAria')}
          className="flex items-center justify-center w-12 h-12 rounded-full bg-navy text-white shadow-md hover:opacity-80 active:scale-95 transition-all duration-150"
        >
          <ArrowRightIcon className="w-5 h-5" strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
}
