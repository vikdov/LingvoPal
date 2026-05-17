import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, LayersIcon, BookOpenIcon, PlayIcon, PlusCircleIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { usePracticeStore } from '../store/practice.store';
import { PracticeCard } from '../components/PracticeCard';
import { formatRelativeTime } from '../utils/formatReviewTime';
import { useTouchSet, useMyLibrary } from '@/features/sets/hooks/useSetsQuery';
import { useAllLanguages } from '@/features/languages';
import { useLanguageStore } from '@/features/languages/store/language.store';
import { langName } from '@/features/sets/utils/formatters';

function PracticeSetPicker() {
  const navigate = useNavigate();
  const touchSet = useTouchSet();
  const { data, isLoading } = useMyLibrary(0, 50);
  const { data: languages = [] } = useAllLanguages();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);

  const entries = data?.data ?? [];
  const withDue = entries.filter((e) => e.due_count > 0);
  const noDue = entries.filter((e) => e.due_count === 0 && e.set.item_count > 0);

  const totalDue = withDue.reduce((sum, e) => sum + e.due_count, 0);
  const activeLangHasDue = withDue.some((e) => e.set.source_lang_id === activeLanguageId);

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col gap-4 items-center justify-center px-6 max-w-lg mx-auto w-full">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-6">
        <p className="text-sm text-muted-foreground">No sets in your library yet.</p>
        <Button onClick={() => navigate('/sets/discover')}>
          <PlusCircleIcon className="size-4" />
          Browse sets
        </Button>
      </div>
    );
  }

  function handlePick(setId: number) {
    touchSet.mutate(setId);
    navigate(`/practice?setId=${setId}`);
  }

  function SetRow({ entry }: { entry: typeof entries[0] }) {
    const { set } = entry;
    return (
      <button
        onClick={() => handlePick(entry.set_id)}
        className="flex items-center justify-between gap-3 w-full rounded-lg border border-border bg-card px-4 py-3 text-left hover:bg-muted/50 transition-colors group"
      >
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground truncate">{set.title}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <LayersIcon className="size-3" />
              {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
            </span>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <BookOpenIcon className="size-3" />
              {langName(set.source_lang_id, languages)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {entry.due_count > 0 ? (
            <Badge className="text-xs tabular-nums">{entry.due_count} due</Badge>
          ) : (
            <span className="text-xs text-muted-foreground">fresh</span>
          )}
          <PlayIcon className="size-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
        </div>
      </button>
    );
  }

  return (
    <div className="flex-1 flex flex-col gap-5 items-center justify-center px-6 py-8 max-w-lg mx-auto w-full">
      {totalDue > 0 && (
        <div className="w-full flex items-center justify-between gap-3 pb-4 border-b border-border">
          <p className="text-sm text-foreground">
            <span className="font-bold tabular-nums">{totalDue}</span>
            <span className="text-muted-foreground">
              {' '}word{totalDue === 1 ? '' : 's'} due across{' '}
              {withDue.length} {withDue.length === 1 ? 'set' : 'sets'}
            </span>
          </p>
          {activeLangHasDue && activeLanguageId && (
            <Button size="sm" onClick={() => navigate(`/practice?all=true&lang=${activeLanguageId}`)}>
              Start all due
            </Button>
          )}
        </div>
      )}

      {withDue.length > 0 && (
        <div className="w-full flex flex-col gap-2">
          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Due for review</p>
          {withDue.map((e) => <SetRow key={e.set_id} entry={e} />)}
        </div>
      )}

      {noDue.length > 0 && (
        <div className="w-full flex flex-col gap-2">
          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
            {withDue.length > 0 ? 'Practice anyway' : 'Your sets'}
          </p>
          {noDue.map((e) => <SetRow key={e.set_id} entry={e} />)}
        </div>
      )}

      <Button variant="outline" size="sm" onClick={() => navigate('/sets')}>
        Manage library
      </Button>
    </div>
  );
}

export function PracticeView() {
  const { phase, error, nextReviewAt, startSession, startSessionAll, reset } = usePracticeStore();
  const store = usePracticeStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const setId = Number(searchParams.get('setId')) || 0;
  const practiceAll = searchParams.get('all') === 'true';
  const sourceLangId = Number(searchParams.get('lang')) || 0;
  const touchSet = useTouchSet();

  useEffect(() => {
    if (phase !== 'idle') {
      // Restored session — check if it matches current URL params.
      const matches = practiceAll
        ? store.practiceAllMode && store.sourceLangId === sourceLangId
        : !store.practiceAllMode && store.setId === setId;
      if (!matches) reset(); // phase → idle, effect re-fires, starts correct session
      return;
    }
    if (practiceAll && sourceLangId > 0) {
      startSessionAll(sourceLangId);
    } else if (setId > 0) {
      startSession(setId);
      touchSet.mutate(setId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, setId, practiceAll, sourceLangId, startSession, startSessionAll, reset]);

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
    return <PracticeSetPicker />;
  }

  return null;
}
