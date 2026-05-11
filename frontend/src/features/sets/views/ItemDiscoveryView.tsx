import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import {
  SearchIcon,
  PlusIcon,
  GitForkIcon,
  LayersIcon,
  FlagIcon,
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
  EmptyMedia,
} from '@/components/ui/empty';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { PaginationBar } from '@/components/ui/pagination-bar';
import { useAllLanguages } from '@/features/languages';
import type { LanguageRef } from '@/features/languages';
import {
  usePublicItems,
  useCreatedSets,
  useAddExistingItemToSet,
  useForkItemIntoSet,
  useReportItem,
} from '../hooks/useSetsQuery';
import type { ItemSummaryResponse, PartOfSpeech } from '../types/sets.types';
import type { ComplaintReason } from '@/features/admin/types/admin.types';
import { Textarea } from '@/components/ui/textarea';

const COMPLAINT_REASONS: { value: ComplaintReason; label: string }[] = [
  { value: 'wrong_language', label: 'Wrong language' },
  { value: 'incorrect_translation', label: 'Incorrect translation' },
  { value: 'inappropriate', label: 'Inappropriate content' },
  { value: 'spam', label: 'Spam' },
  { value: 'duplicate', label: 'Duplicate' },
  { value: 'other', label: 'Other' },
];

interface ReportItemDialogProps {
  itemId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function ReportItemDialog({ itemId, open, onOpenChange }: ReportItemDialogProps) {
  const [reason, setReason] = useState<ComplaintReason | ''>('');
  const [details, setDetails] = useState('');
  const report = useReportItem();

  function handleSubmit() {
    if (!reason) return;
    report.mutate(
      { itemId, reason, details: details.trim() || undefined },
      {
        onSuccess: () => {
          toast.success('Report submitted. Thank you.');
          onOpenChange(false);
          setReason('');
          setDetails('');
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Report this expression</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-1">
          <Select value={reason} onValueChange={(v) => setReason(v as ComplaintReason)}>
            <SelectTrigger>
              <SelectValue placeholder="Select a reason…" />
            </SelectTrigger>
            <SelectContent>
              {COMPLAINT_REASONS.map((r) => (
                <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Textarea
            placeholder="Additional details (optional)"
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            rows={3}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={report.isPending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleSubmit}
            disabled={!reason || report.isPending}
          >
            {report.isPending ? 'Submitting…' : 'Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PAGE_SIZE_OPTIONS = [20, 50, 100] as const;
const DEFAULT_PAGE_SIZE = 20;

const PART_OF_SPEECH_OPTIONS: { value: PartOfSpeech; label: string }[] = [
  { value: 'noun', label: 'Noun' },
  { value: 'verb', label: 'Verb' },
  { value: 'adjective', label: 'Adjective' },
  { value: 'adverb', label: 'Adverb' },
  { value: 'pronoun', label: 'Pronoun' },
  { value: 'preposition', label: 'Preposition' },
  { value: 'conjunction', label: 'Conjunction' },
  { value: 'interjection', label: 'Interjection' },
  { value: 'article', label: 'Article' },
  { value: 'other', label: 'Other' },
];

const DIFFICULTY_OPTIONS = [
  { value: '1', label: 'A1 — Beginner' },
  { value: '2', label: 'A2 — Elementary' },
  { value: '3', label: 'B1 — Intermediate' },
  { value: '4', label: 'B2 — Upper intermediate' },
  { value: '5', label: 'C1 — Advanced' },
  { value: '6', label: 'C2 — Proficient' },
  { value: '7', label: 'Native' },
];

function difficultyLabel(d: number): string {
  const labels = ['', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Native'];
  return labels[d] ?? String(d);
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function ItemCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-1/2" />
        <Skeleton className="h-4 w-3/4" />
      </CardHeader>
      <CardContent className="flex gap-2">
        <Skeleton className="h-5 w-14" />
        <Skeleton className="h-5 w-10" />
      </CardContent>
      <CardFooter className="gap-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-16" />
      </CardFooter>
    </Card>
  );
}

// ── AddToSetDialog ────────────────────────────────────────────────────────────

interface AddToSetDialogProps {
  item: ItemSummaryResponse;
  mode: 'add' | 'fork';
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function AddToSetDialog({ item, mode, open, onOpenChange }: AddToSetDialogProps) {
  const [selectedSetId, setSelectedSetId] = useState('');
  const { data: setsData, isLoading: setsLoading } = useCreatedSets(0, 100);
  const addItem = useAddExistingItemToSet();
  const forkItem = useForkItemIntoSet();

  const isPending = addItem.isPending || forkItem.isPending;

  useEffect(() => {
    if (open) setSelectedSetId('');
  }, [open]);

  function handleConfirm() {
    if (!selectedSetId) return;
    const setId = Number(selectedSetId);

    if (mode === 'add') {
      addItem.mutate(
        { setId, itemId: item.id },
        {
          onSuccess: () => {
            const setTitle = setsData?.data.find((s) => s.id === setId)?.title ?? 'set';
            toast.success(`"${item.term}" added to ${setTitle}.`);
            onOpenChange(false);
          },
          onError: (err) => toast.error(err.message),
        },
      );
    } else {
      forkItem.mutate(
        { setId, itemId: item.id },
        {
          onSuccess: () => {
            const setTitle = setsData?.data.find((s) => s.id === setId)?.title ?? 'set';
            toast.success(`"${item.term}" forked into ${setTitle}. Edit it freely.`);
            onOpenChange(false);
          },
          onError: (err) => toast.error(err.message),
        },
      );
    }
  }

  const sets = setsData?.data ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>
            {mode === 'add' ? 'Add to set' : 'Fork into set'}
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-3 py-1">
          <p className="text-sm text-muted-foreground">
            {mode === 'add'
              ? `"${item.term}" will be added as-is. You can study it but not edit it.`
              : `"${item.term}" will be copied into your set. You can edit the copy freely.`}
          </p>

          <Select
            value={selectedSetId}
            onValueChange={setSelectedSetId}
            disabled={setsLoading || isPending}
          >
            <SelectTrigger>
              <SelectValue placeholder="Choose a set…" />
            </SelectTrigger>
            <SelectContent>
              {sets.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                  No sets found. Create one first.
                </div>
              )}
              {sets.map((s) => (
                <SelectItem key={s.id} value={String(s.id)}>
                  {s.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!selectedSetId || isPending || sets.length === 0}
          >
            {isPending
              ? 'Working…'
              : mode === 'add'
              ? 'Add to Set'
              : 'Fork'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── DiscoveryItemCard ─────────────────────────────────────────────────────────

interface DiscoveryItemCardProps {
  item: ItemSummaryResponse;
  languages: LanguageRef[];
}

function DiscoveryItemCard({ item, languages }: DiscoveryItemCardProps) {
  const [dialogMode, setDialogMode] = useState<'add' | 'fork' | null>(null);
  const [reportOpen, setReportOpen] = useState(false);

  const langName =
    languages.find((l) => l.id === item.language_id)?.name ??
    `Language ${item.language_id}`;

  return (
    <>
      <Card className="flex flex-col overflow-hidden">
        {item.image_url && (
          <div className="aspect-video w-full overflow-hidden">
            <img
              src={item.image_url}
              alt={item.term}
              className="h-full w-full object-cover"
            />
          </div>
        )}

        <CardHeader className="flex-1 pb-2">
          <CardTitle className="text-base">{item.term}</CardTitle>
          {item.context && (
            <CardDescription className="line-clamp-2 italic">
              &ldquo;{item.context}&rdquo;
            </CardDescription>
          )}
        </CardHeader>

        <CardContent className="flex flex-wrap gap-1.5 pb-3 pt-0">
          <Badge variant="outline" className="text-xs">
            {langName}
          </Badge>
          {item.part_of_speech && (
            <Badge variant="outline" className="text-xs">
              {item.part_of_speech}
            </Badge>
          )}
          {item.difficulty != null && (
            <Badge variant="secondary" className="text-xs">
              {difficultyLabel(item.difficulty)}
            </Badge>
          )}
        </CardContent>

        <CardFooter className="gap-2 pt-0">
          <Button size="sm" onClick={() => setDialogMode('add')}>
            <PlusIcon className="size-3.5" />
            Add to Set
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setDialogMode('fork')}>
            <GitForkIcon className="size-3.5" />
            Fork
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="ml-auto text-muted-foreground"
            onClick={() => setReportOpen(true)}
          >
            <FlagIcon className="size-3.5" />
          </Button>
        </CardFooter>
      </Card>

      {dialogMode && (
        <AddToSetDialog
          item={item}
          mode={dialogMode}
          open
          onOpenChange={(open) => !open && setDialogMode(null)}
        />
      )}

      <ReportItemDialog
        itemId={item.id}
        open={reportOpen}
        onOpenChange={setReportOpen}
      />
    </>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function ItemDiscoveryView() {
  const [inputValue, setInputValue] = useState('');
  const [query, setQuery] = useState('');
  const [languageId, setLanguageId] = useState('any');
  const [partOfSpeech, setPartOfSpeech] = useState('any');
  const [difficulty, setDifficulty] = useState('any');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const resultsSectionRef = useRef<HTMLDivElement>(null);
  const isFirstRender = useRef(true);

  const { data: languages = [] } = useAllLanguages();

  // Debounce search input; reset to page 1 on new query
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setQuery(inputValue);
      setPage(1);
    }, 400);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [inputValue]);

  // Scroll results into view on page/pageSize change (skip initial mount)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    resultsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [page, pageSize]);

  const skip = (page - 1) * pageSize;

  const { data, isLoading, isFetching, isError, error } = usePublicItems({
    query: query || undefined,
    language_id: languageId !== 'any' ? Number(languageId) : null,
    part_of_speech: partOfSpeech !== 'any' ? (partOfSpeech as PartOfSpeech) : null,
    difficulty: difficulty !== 'any' ? Number(difficulty) : null,
    skip,
    limit: pageSize,
  });

  function handleFilterChange(setter: (v: string) => void) {
    return (v: string) => {
      setter(v);
      setPage(1);
    };
  }

  function handlePageChange(newPage: number) {
    setPage(newPage);
  }

  function handlePageSizeChange(newSize: number) {
    setPageSize(newSize);
    setPage(1);
  }

  const items = data?.data ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 0;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Find Expressions</h1>
        <p className="text-sm text-muted-foreground">
          Search public vocabulary and add expressions to your sets.
        </p>
      </div>

      {/* ── Filters ─────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3">
        <div className="relative min-w-[200px] flex-1">
          <SearchIcon className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Search expressions…"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
        </div>

        <Select value={languageId} onValueChange={handleFilterChange(setLanguageId)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Language" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any language</SelectItem>
            {languages.map((l) => (
              <SelectItem key={l.id} value={String(l.id)}>
                {l.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={partOfSpeech} onValueChange={handleFilterChange(setPartOfSpeech)}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Part of speech" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any part of speech</SelectItem>
            {PART_OF_SPEECH_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={difficulty} onValueChange={handleFilterChange(setDifficulty)}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Difficulty" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any difficulty</SelectItem>
            {DIFFICULTY_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* ── Results ─────────────────────────────────────────────────────── */}
      <div ref={resultsSectionRef} className="flex flex-col gap-4 scroll-mt-4">
        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: Math.min(pageSize, 9) }).map((_, i) => (
              <ItemCardSkeleton key={i} />
            ))}
          </div>
        )}

        {isError && (
          <Empty>
            <EmptyHeader>
              <EmptyTitle>Failed to load expressions</EmptyTitle>
              <EmptyDescription>{error.message}</EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}

        {!isLoading && !isError && items.length === 0 && (
          <Empty>
            <EmptyMedia variant="icon">
              <LayersIcon className="size-4" />
            </EmptyMedia>
            <EmptyHeader>
              <EmptyTitle>No expressions found</EmptyTitle>
              <EmptyDescription>
                {query
                  ? `No public expressions match "${query}". Try different filters.`
                  : 'No public vocabulary is available yet.'}
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}

        {!isLoading && !isError && items.length > 0 && (
          <>
            <div
              className={`grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 transition-opacity duration-150 ${isFetching ? 'opacity-60' : 'opacity-100'}`}
            >
              {items.map((item) => (
                <DiscoveryItemCard key={item.id} item={item} languages={languages} />
              ))}
            </div>

            <PaginationBar
              page={page}
              pages={pages}
              pageSize={pageSize}
              pageSizeOptions={PAGE_SIZE_OPTIONS}
              total={total}
              skip={skip}
              isFetching={isFetching}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          </>
        )}
      </div>
    </div>
  );
}
