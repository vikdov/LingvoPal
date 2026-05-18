import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, PenLine, CalendarClock, BarChart3, Check, ArrowRight, ChevronLeft, Layers } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useAllLanguages, useAddUserLanguage } from '../hooks/useUserLanguages';
import { usePublicSets, useAddToLibrary } from '@/features/sets/hooks/useSetsQuery';
import { difficultyLabel } from '@/features/sets/utils/formatters';
import type { SetSummaryResponse } from '@/features/sets/types/sets.types';

// ── Step dots ─────────────────────────────────────────────────────────────────

function StepDots({ current }: { current: 1 | 2 }) {
  return (
    <div className="flex items-center gap-1.5">
      {([1, 2] as const).map((n) => (
        <span
          key={n}
          className={`rounded-full transition-all duration-200 ${
            n === current
              ? 'w-5 h-1.5 bg-primary'
              : n < current
              ? 'w-1.5 h-1.5 bg-primary/40'
              : 'w-1.5 h-1.5 bg-border'
          }`}
        />
      ))}
    </div>
  );
}

// ── Starter set card ──────────────────────────────────────────────────────────

function StarterSetCard({
  set,
  onAdd,
  added,
  pending,
}: {
  set: SetSummaryResponse;
  onAdd: () => void;
  added: boolean;
  pending: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-4 py-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          {set.status === 'official' && (
            <Badge
              variant="outline"
              className="shrink-0 font-mono text-[9px] px-1 py-0 border-primary/40 text-primary"
            >
              official
            </Badge>
          )}
          <p className="text-sm font-medium text-foreground truncate">{set.title}</p>
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Layers className="size-3" />
            {set.item_count} words
          </span>
          {set.difficulty != null && (
            <span className="text-xs font-mono text-muted-foreground">
              {difficultyLabel(set.difficulty)}
            </span>
          )}
        </div>
      </div>
      <Button
        size="sm"
        variant={added ? 'ghost' : 'outline'}
        onClick={onAdd}
        disabled={added || pending}
        className={added ? 'text-green-600 dark:text-green-400 pointer-events-none' : ''}
      >
        {added ? (
          <>
            <Check className="size-3.5 mr-1" />
            Added
          </>
        ) : (
          'Add'
        )}
      </Button>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function AddFirstLanguagePrompt() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1);
  const [selectedLangId, setSelectedLangId] = useState<number | null>(null);
  const [addedSetIds, setAddedSetIds] = useState<Set<number>>(new Set());
  const [pendingSetId, setPendingSetId] = useState<number | null>(null);
  const [firstAddedSetId, setFirstAddedSetId] = useState<number | null>(null);

  const { data: allLanguages = [], isLoading: loadingLangs } = useAllLanguages();
  const addLanguage = useAddUserLanguage();
  const addToLibrary = useAddToLibrary();

  const { data: publicSetsData, isLoading: loadingSets } = usePublicSets({
    source_lang_id: selectedLangId,
    limit: 6,
  });
  const starterSets = publicSetsData?.data ?? [];

  function handleContinue() {
    if (!selectedLangId) return;
    addLanguage.mutate(
      { language_id: selectedLangId, set_active: true },
      { onSuccess: () => setStep(2) },
    );
  }

  function handleAddSet(setId: number) {
    setPendingSetId(setId);
    addToLibrary.mutate(setId, {
      onSuccess: () => {
        setAddedSetIds((prev) => new Set(prev).add(setId));
        if (!firstAddedSetId) setFirstAddedSetId(setId);
        setPendingSetId(null);
      },
      onError: () => setPendingSetId(null),
    });
  }

  const hasAdded = addedSetIds.size > 0;
  const selectedLangName = allLanguages.find((l) => l.id === selectedLangId)?.name ?? '';

  // ── Step 1 ──────────────────────────────────────────────────────────────────

  if (step === 1) {
    return (
      <div className="flex flex-col items-center justify-center gap-8 py-20 text-center px-6">
        <StepDots current={1} />

        <div className="flex flex-col items-center gap-3">
          <div className="size-14 rounded-full bg-primary/10 flex items-center justify-center">
            <Globe className="size-6 text-primary" />
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-foreground">
            What are you learning?
          </h2>
          <p className="text-sm text-muted-foreground max-w-[34ch] leading-relaxed">
            Pick your first language. You can add more later.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2 items-center">
          <Select
            value={selectedLangId ? String(selectedLangId) : ''}
            onValueChange={(v) => setSelectedLangId(Number(v))}
            disabled={loadingLangs}
          >
            <SelectTrigger className="w-52">
              <SelectValue placeholder="Select a language…" />
            </SelectTrigger>
            <SelectContent>
              {allLanguages.map((l) => (
                <SelectItem key={l.id} value={String(l.id)}>
                  {l.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleContinue}
            disabled={!selectedLangId || addLanguage.isPending}
          >
            {addLanguage.isPending ? 'Setting up…' : 'Continue'}
            {!addLanguage.isPending && <ArrowRight className="size-3.5 ml-1" />}
          </Button>
        </div>
      </div>
    );
  }

  // ── Step 2 ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col items-center gap-8 py-12 px-6 max-w-xl mx-auto w-full">
      <StepDots current={2} />

      {/* Core loop explainer */}
      <div className="w-full flex flex-col gap-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold tracking-tight text-foreground">
            Here's how it works
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Three things, then you're practicing.
          </p>
        </div>

        {/* Visual practice card mockup */}
        <div className="rounded-xl border border-border bg-muted/30 p-5 flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
              Practice card
            </span>
            <p className="text-base text-foreground leading-relaxed">
              Da bambino,{' '}
              <span className="inline-block border-b-2 border-primary min-w-[80px] text-center text-primary font-medium">
                leggevo
              </span>{' '}
              ogni sera.
            </p>
            <p className="text-xs text-muted-foreground italic mt-1">
              "As a child, I used to read every evening."
            </p>
          </div>

          <div className="h-px bg-border" />

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="size-5 rounded-full bg-green-500/15 flex items-center justify-center shrink-0">
              <Check className="size-3 text-green-600 dark:text-green-400" />
            </span>
            Correct — next review in <span className="text-foreground font-medium ml-1">1 day</span>
          </div>
        </div>

        {/* 3 key points */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            {
              icon: PenLine,
              title: 'Active recall',
              body: 'Type the word from memory — no multiple choice.',
            },
            {
              icon: CalendarClock,
              title: 'Spaced repetition',
              body: 'SM-2 schedules reviews so you never forget.',
            },
            {
              icon: BarChart3,
              title: 'Track mastery',
              body: 'Words progress from new → learning → mature.',
            },
          ].map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="flex flex-col gap-1.5 rounded-lg border border-border bg-card p-3"
            >
              <Icon className="size-4 text-primary" />
              <p className="text-sm font-medium text-foreground">{title}</p>
              <p className="text-xs text-muted-foreground leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Starter sets */}
      <div className="w-full flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-foreground">
            Starter sets for {selectedLangName}
          </p>
          <button
            onClick={() =>
              navigate(`/sets/discover?source_lang=${selectedLangId}`)
            }
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Browse all →
          </button>
        </div>

        {loadingSets ? (
          <div className="flex flex-col gap-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-[62px] rounded-lg" />
            ))}
          </div>
        ) : starterSets.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-6 text-center flex flex-col gap-2">
            <p className="text-sm text-muted-foreground">
              No starter sets yet for {selectedLangName}.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/sets/discover')}
            >
              Browse community sets
            </Button>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {starterSets.map((set) => (
              <StarterSetCard
                key={set.id}
                set={set}
                added={addedSetIds.has(set.id)}
                pending={pendingSetId === set.id}
                onAdd={() => handleAddSet(set.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Bottom CTAs */}
      <div className="w-full flex flex-col gap-2">
        {hasAdded ? (
          <Button
            className="w-full"
            onClick={() =>
              navigate(
                firstAddedSetId
                  ? `/practice?setId=${firstAddedSetId}`
                  : '/practice',
              )
            }
          >
            <PenLine className="size-4 mr-1.5" />
            Start practicing
          </Button>
        ) : (
          <Button
            className="w-full"
            variant="outline"
            onClick={() => navigate(`/sets/discover?source_lang=${selectedLangId}`)}
          >
            Find sets to study
          </Button>
        )}
        <button
          onClick={() => setStep(1)}
          className="flex items-center justify-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors py-1"
        >
          <ChevronLeft className="size-3" />
          Change language
        </button>
      </div>
    </div>
  );
}
