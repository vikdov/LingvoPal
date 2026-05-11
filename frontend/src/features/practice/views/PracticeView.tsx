import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { usePracticeStore } from '../store/practice.store';
import { PracticeCard } from '../components/PracticeCard';
import { formatRelativeTime } from '../utils/formatReviewTime';
import { useTouchSet } from '@/features/sets/hooks/useSetsQuery';

export function PracticeView() {
  const { phase, error, nextReviewAt, startSession, startSessionAll, reset } = usePracticeStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const setId = Number(searchParams.get('setId')) || 0;
  const practiceAll = searchParams.get('all') === 'true';
  const sourceLangId = Number(searchParams.get('lang')) || 0;
  const touchSet = useTouchSet();

  useEffect(() => {
    if (phase !== 'idle') return;
    if (practiceAll && sourceLangId > 0) {
      startSessionAll(sourceLangId);
    } else if (setId > 0) {
      startSession(setId);
      touchSet.mutate(setId);
    }
  }, [phase, setId, practiceAll, sourceLangId, startSession, startSessionAll]);

  useEffect(() => {
    if (phase === 'complete') {
      navigate('/practice/summary', { replace: true });
    }
  }, [phase, navigate]);

  if (phase === 'loading') {
    return (
      <div className="flex-1 flex items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>Loading session…</span>
      </div>
    );
  }

  if (phase === 'finalising') {
    return (
      <div className="flex-1 flex items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>Saving results…</span>
      </div>
    );
  }

  if (phase === 'no_due_items') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-base font-medium">All caught up!</p>
        <p className="text-sm text-muted-foreground">
          {nextReviewAt
            ? `Next review ${formatRelativeTime(nextReviewAt, true)}`
            : 'No items due right now.'}
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (practiceAll && sourceLangId > 0) startSessionAll(sourceLangId, true);
              else if (setId > 0) startSession(setId, true);
            }}
            className="px-4 py-2 rounded-md border border-border text-sm hover:bg-muted transition-colors"
          >
            Practice anyway
          </button>
          <button
            onClick={() => navigate(setId > 0 ? '/sets' : '/')}
            className="px-4 py-2 rounded-md border border-border text-sm hover:bg-muted transition-colors"
          >
            {setId > 0 ? 'Back to library' : 'Dashboard'}
          </button>
        </div>
      </div>
    );
  }

  if (phase === 'error') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-sm text-muted-foreground">{error ?? 'Something went wrong.'}</p>
        <button
          onClick={() => {
            reset();
            if (practiceAll && sourceLangId > 0) startSessionAll(sourceLangId);
            else if (setId > 0) startSession(setId);
          }}
          className="px-4 py-2 rounded-md border border-border text-sm hover:bg-muted transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  if (phase === 'active') {
    return <PracticeCard />;
  }

  if (!setId && !practiceAll) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-6">
        <p className="text-sm text-muted-foreground">Select a set to start practicing.</p>
        <button
          onClick={() => navigate('/sets')}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm hover:opacity-90 transition-opacity"
        >
          Browse sets
        </button>
      </div>
    );
  }

  return null;
}
