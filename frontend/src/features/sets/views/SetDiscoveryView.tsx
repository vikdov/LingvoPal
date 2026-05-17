import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { SearchIcon, PlusIcon, LayersIcon, BookOpenIcon, FlagIcon, UserIcon, CopyIcon } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { SetCover } from '../components/SetCover';
import { Skeleton } from '@/components/ui/skeleton';
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
} from '@/components/ui/pagination';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useAllLanguages } from '@/features/languages';
import type { LanguageRef } from '@/features/languages';
import { usePublicSets, useAddToLibrary, useForkSet } from '../hooks/useSetsQuery';
import { DiscoveryTabs } from '../components/DiscoveryTabs';
import { ReportDialog } from '../components/ReportDialog';
import type { SetSummaryResponse } from '../types/sets.types';

function langName(id: number | null | undefined, languages: LanguageRef[]): string {
  if (id == null) return '';
  return languages.find((l) => l.id === id)?.name ?? String(id);
}

function langCode(id: number | null | undefined, languages: LanguageRef[]): string {
  if (id == null) return '';
  return languages.find((l) => l.id === id)?.code ?? '';
}

const PAGE_SIZE = 12;

const DIFFICULTY_OPTIONS = [
  { value: 'any', label: 'Any difficulty' },
  { value: '1', label: 'A1 – Beginner' },
  { value: '2', label: 'A2 – Elementary' },
  { value: '3', label: 'B1 – Intermediate' },
  { value: '4', label: 'B2 – Upper-Intermediate' },
  { value: '5', label: 'C1 – Advanced' },
  { value: '6', label: 'C2 – Proficiency' },
  { value: '7', label: 'Native' },
];

function difficultyLabel(difficulty: number | null): string {
  if (difficulty === null) return '';
  const labels = ['', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Native'];
  return labels[difficulty] ?? String(difficulty);
}

function SetCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-3/4" />
      </CardHeader>
      <CardContent className="flex gap-2">
        <Skeleton className="h-5 w-10" />
        <Skeleton className="h-5 w-14" />
      </CardContent>
      <CardFooter className="gap-2">
        <Skeleton className="h-8 w-28" />
        <Skeleton className="h-8 w-16" />
      </CardFooter>
    </Card>
  );
}

interface DiscoverySetCardProps {
  set: SetSummaryResponse;
  inLibrary: boolean;
  onAddedToLibrary: (setId: number) => void;
  languages: LanguageRef[];
}

function DiscoverySetCard({ set, inLibrary, onAddedToLibrary, languages }: DiscoverySetCardProps) {
  const navigate = useNavigate();
  const addToLibrary = useAddToLibrary();
  const forkSet = useForkSet();
  const [reportOpen, setReportOpen] = useState(false);

  function handleAddToLibrary() {
    addToLibrary.mutate(set.id, {
      onSuccess: () => {
        toast.success('Added to library.');
        onAddedToLibrary(set.id);
      },
      onError: (err) => toast.error(err.message),
    });
  }

  function handleFork() {
    forkSet.mutate(set.id, {
      onSuccess: (forked) => {
        toast.success('Set forked. Redirecting…');
        navigate(`/sets/${forked.id}`);
      },
      onError: (err) => toast.error(err.message),
    });
  }

  return (
    <>
      <Card
        className="h-full overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => navigate(`/sets/${set.id}`)}
      >
        <SetCover
          langCode={langCode(set.source_lang_id, languages)}
          langName={langName(set.source_lang_id, languages)}
          setId={set.id}
        />
        <CardHeader>
          <CardTitle className="line-clamp-2">
            {set.title}
          </CardTitle>
        </CardHeader>

        <CardContent className="flex flex-wrap gap-2">
          {set.difficulty !== null && (
            <Badge variant="secondary">{difficultyLabel(set.difficulty)}</Badge>
          )}
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <LayersIcon className="size-3" />
            {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
          </span>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <BookOpenIcon className="size-3" />
            {langName(set.source_lang_id, languages)}{set.target_lang_id != null ? ` → ${langName(set.target_lang_id, languages)}` : ''}
          </span>
          {set.creator_username && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <UserIcon className="size-3" />
              {set.creator_username}
            </span>
          )}
        </CardContent>

        <CardFooter className="gap-2" onClick={(e) => e.stopPropagation()}>
          {inLibrary ? (
            <Button size="sm" variant="secondary" disabled>
              In Library
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleAddToLibrary}
              disabled={addToLibrary.isPending}
            >
              <PlusIcon />
              Add to Library
            </Button>
          )}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleFork}
                  disabled={forkSet.isPending}
                >
                  <CopyIcon className="size-3.5" />
                  Copy to My Sets
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Creates an editable copy in your sets</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="sm"
                  variant="ghost"
                  className="ml-auto text-muted-foreground hover:text-destructive"
                  onClick={() => setReportOpen(true)}
                >
                  <FlagIcon className="size-3.5" />
                  <span className="sr-only">Report</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Report this set</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardFooter>
      </Card>

      <ReportDialog
        targetId={set.id}
        targetType="set"
        open={reportOpen}
        onOpenChange={setReportOpen}
      />
    </>
  );
}

export function SetDiscoveryView() {
  const [inputValue, setInputValue] = useState('');
  const [query, setQuery] = useState('');
  const [difficulty, setDifficulty] = useState('any');
  const [langFilter, setLangFilter] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Track which set IDs have been added to library in this session
  const [addedToLibrary, setAddedToLibrary] = useState<Set<number>>(new Set());
  const { data: languages = [] } = useAllLanguages();

  // Debounce the search input
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

  const skip = (page - 1) * PAGE_SIZE;
  const { data, isLoading, isError, error } = usePublicSets({
    query: query || undefined,
    source_lang_id: langFilter,
    skip,
    limit: PAGE_SIZE,
  });

  function handleAddedToLibrary(setId: number) {
    setAddedToLibrary((prev) => new Set([...prev, setId]));
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Discover</h1>
        <p className="text-sm text-muted-foreground">
          Browse public vocabulary sets and expressions created by the community.
        </p>
      </div>

      <DiscoveryTabs />

      {/* Filters */}
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <SearchIcon className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            <Input
              className="pl-8"
              placeholder="Search sets…"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
          </div>

          <Select value={difficulty} onValueChange={(v) => { setDifficulty(v); setPage(1); }}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DIFFICULTY_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {languages.length > 0 && (
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            spacing={1}
            value={langFilter == null ? 'all' : String(langFilter)}
            onValueChange={(v) => { setLangFilter(v === 'all' || v === '' ? null : Number(v)); setPage(1); }}
            className="flex-wrap justify-start"
          >
            <ToggleGroupItem value="all">All languages</ToggleGroupItem>
            {languages.map((l) => (
              <ToggleGroupItem key={l.id} value={String(l.id)}>{l.name}</ToggleGroupItem>
            ))}
          </ToggleGroup>
        )}
      </div>

      {/* Results */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <SetCardSkeleton key={i} />
          ))}
        </div>
      )}

      {isError && (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>Failed to load sets</EmptyTitle>
            <EmptyDescription>{error.message}</EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}

      {!isLoading && !isError && data && data.data.length === 0 && (
        <Empty>
          <EmptyMedia variant="icon">
            <SearchIcon className="size-4" />
          </EmptyMedia>
          <EmptyHeader>
            <EmptyTitle>No sets found</EmptyTitle>
            <EmptyDescription>
              {query
                ? `No public sets match "${query}". Try different keywords.`
                : 'There are no public sets available yet.'}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      )}

      {!isLoading && !isError && data && data.data.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.data.map((set: SetSummaryResponse) => (
              <DiscoverySetCard
                key={set.id}
                set={set}
                inLibrary={addedToLibrary.has(set.id)}
                onAddedToLibrary={handleAddedToLibrary}
                languages={languages}
              />
            ))}
          </div>

          {data.pages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    aria-disabled={page === 1}
                    className={page === 1 ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
                <PaginationItem>
                  <PaginationNext
                    onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                    aria-disabled={page === data.pages}
                    className={page === data.pages ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      )}
    </div>
  );
}
