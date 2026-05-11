import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { PlusIcon, BookmarkIcon, BookmarkCheckIcon, BookOpenIcon, LayersIcon, DownloadIcon, PinIcon, PlayIcon } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
} from '@/components/ui/pagination';
import { useAllLanguages } from '@/features/languages';
import { useLanguageStore } from '@/features/languages/store/language.store';
import type { LanguageRef } from '@/features/languages';
import { useMyLibrary, useCreatedSets, useRemoveFromLibrary, usePinSet, useTouchSet } from '../hooks/useSetsQuery';
import { langAccentColor } from '../components/SetCover';
import { SetEditor } from '../components/SetEditor';
import { AnkiImportModal } from '../components/AnkiImportModal';
import type { SetLibraryEntry, CreatedSetSummaryResponse } from '../types/sets.types';

function langName(id: number | null | undefined, languages: LanguageRef[]): string {
  if (id == null) return '';
  return languages.find((l) => l.id === id)?.name ?? String(id);
}

const PAGE_SIZE = 12;

function difficultyLabel(difficulty: number | null): string {
  if (difficulty === null) return '';
  const labels = ['', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Native'];
  return labels[difficulty] ?? String(difficulty);
}

function formatDate(iso: string | null): string {
  if (!iso) return 'Never';
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(iso));
}

// ── Language filter bar ───────────────────────────────────────────────────────

interface LangFilterBarProps {
  langIds: number[];
  languages: LanguageRef[];
  value: number | null;
  onChange: (id: number | null) => void;
}

function LangFilterBar({ langIds, languages, value, onChange }: LangFilterBarProps) {
  if (langIds.length < 2) return null;

  return (
    <ToggleGroup
      type="single"
      variant="outline"
      size="sm"
      spacing={1}
      value={value == null ? 'all' : String(value)}
      onValueChange={(v) => onChange(v === 'all' || v === '' ? null : Number(v))}
      className="flex-wrap"
    >
      <ToggleGroupItem value="all">All</ToggleGroupItem>
      {langIds.map((id) => (
        <ToggleGroupItem key={id} value={String(id)}>
          {langName(id, languages)}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

// ── Library tab ───────────────────────────────────────────────────────────────

function LibraryCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </CardHeader>
      <CardContent className="flex gap-2">
        <Skeleton className="h-5 w-12" />
        <Skeleton className="h-5 w-16" />
      </CardContent>
      <CardFooter className="gap-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-24" />
      </CardFooter>
    </Card>
  );
}

interface LibraryEntryCardProps {
  entry: SetLibraryEntry;
  languages: LanguageRef[];
}

function LibraryEntryCard({ entry, languages }: LibraryEntryCardProps) {
  const navigate = useNavigate();
  const removeFromLibrary = useRemoveFromLibrary();
  const pinSet = usePinSet();
  const touchSet = useTouchSet();
  const { set } = entry;

  function handleRemove() {
    if (!window.confirm(`Remove "${set.title}" from your library?`)) return;
    removeFromLibrary.mutate(entry.set_id, {
      onSuccess: () => toast.success('Removed from library.'),
      onError: (err) => toast.error(err.message),
    });
  }

  function handlePinToggle() {
    pinSet.mutate(
      { setId: entry.set_id, is_pinned: !entry.is_pinned },
      { onError: (err) => toast.error(err.message) },
    );
  }

  const accentColor = langAccentColor(
    languages.find((l) => l.id === set.source_lang_id)?.code ?? '',
    entry.set_id,
  );

  return (
    <Card
      className="h-full border-l-4 cursor-pointer transition-shadow hover:shadow-md"
      style={{ borderLeftColor: accentColor }}
      onClick={() => { touchSet.mutate(entry.set_id); navigate(`/sets/${entry.set_id}`); }}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2 flex-1">{set.title}</CardTitle>
          <Button
            size="icon-sm"
            variant="ghost"
            onClick={(e) => { e.stopPropagation(); handlePinToggle(); }}
            disabled={pinSet.isPending}
            title={entry.is_pinned ? 'Unpin' : 'Pin'}
          >
            {entry.is_pinned ? (
              <BookmarkCheckIcon className="size-4 text-primary" />
            ) : (
              <PinIcon className="size-4" />
            )}
            <span className="sr-only">{entry.is_pinned ? 'Unpin' : 'Pin'}</span>
          </Button>
        </div>
        <CardDescription>
          Last opened: {formatDate(entry.last_opened_at)}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-wrap gap-2">
        {set.difficulty !== null && (
          <Badge variant="secondary">{difficultyLabel(set.difficulty)}</Badge>
        )}
        <Badge variant="outline" className="text-xs">
          <BookOpenIcon className="size-3" />
          {langName(set.source_lang_id, languages)}
          {set.target_lang_id != null ? ` → ${langName(set.target_lang_id, languages)}` : ''}
        </Badge>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <LayersIcon className="size-3" />
          {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
        </span>
      </CardContent>

      <CardFooter className="gap-2">
        <Button
          size="sm"
          onClick={(e) => { e.stopPropagation(); touchSet.mutate(entry.set_id); navigate(`/practice?setId=${entry.set_id}`); }}
          disabled={set.item_count === 0}
          title={set.item_count === 0 ? 'No items to study' : undefined}
        >
          Study
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="ml-auto text-destructive hover:text-destructive"
          onClick={(e) => { e.stopPropagation(); handleRemove(); }}
          disabled={removeFromLibrary.isPending}
        >
          Remove
        </Button>
      </CardFooter>
    </Card>
  );
}

function LibraryTab() {
  const [page, setPage] = useState(1);
  const skip = (page - 1) * PAGE_SIZE;
  const { data, isLoading, isError, error } = useMyLibrary(skip, PAGE_SIZE);
  const { data: languages = [] } = useAllLanguages();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);
  const [filterLangId, setFilterLangId] = useState<number | null>(activeLanguageId);

  useEffect(() => {
    setFilterLangId(activeLanguageId);
    setPage(1);
  }, [activeLanguageId]);

  const uniqueLangIds = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.data.map((e) => e.set.source_lang_id))];
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (filterLangId == null) return data.data;
    return data.data.filter((e) => e.set.source_lang_id === filterLangId);
  }, [data, filterLangId]);

  function handleFilterChange(id: number | null) {
    setFilterLangId(id);
    setPage(1);
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <LibraryCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyTitle>Failed to load library</EmptyTitle>
          <EmptyDescription>{error.message}</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <BookmarkIcon />
        </EmptyMedia>
        <EmptyHeader>
          <EmptyTitle>Your library is empty</EmptyTitle>
          <EmptyDescription>
            Discover sets and add them to your library to study them here.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <LangFilterBar
        langIds={uniqueLangIds}
        languages={languages}
        value={filterLangId}
        onChange={handleFilterChange}
      />

      {filtered.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No sets for this language</EmptyTitle>
            <EmptyDescription>Try a different filter or add more sets to your library.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((entry) => (
              <LibraryEntryCard key={entry.set_id} entry={entry} languages={languages} />
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
        </div>
      )}
    </div>
  );
}

// ── Created tab ───────────────────────────────────────────────────────────────

interface CreatedSetCardProps {
  set: CreatedSetSummaryResponse;
  languages: LanguageRef[];
}

function CreatedSetCard({ set, languages }: CreatedSetCardProps) {
  const navigate = useNavigate();
  const pinSet = usePinSet();
  const touchSet = useTouchSet();

  function handlePinToggle() {
    pinSet.mutate(
      { setId: set.id, is_pinned: !set.is_pinned },
      { onError: (err) => toast.error(err.message) },
    );
  }

  const accentColor = langAccentColor(
    languages.find((l) => l.id === set.source_lang_id)?.code ?? '',
    set.id,
  );

  return (
    <Card
      className="h-full border-l-4 cursor-pointer transition-shadow hover:shadow-md"
      style={{ borderLeftColor: accentColor }}
      onClick={() => { touchSet.mutate(set.id); navigate(`/sets/${set.id}`); }}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2 flex-1">{set.title}</CardTitle>
          <Button
            size="icon-sm"
            variant="ghost"
            onClick={(e) => { e.stopPropagation(); handlePinToggle(); }}
            disabled={pinSet.isPending}
            title={set.is_pinned ? 'Unpin' : 'Pin'}
          >
            {set.is_pinned ? (
              <BookmarkCheckIcon className="size-4 text-primary" />
            ) : (
              <PinIcon className="size-4" />
            )}
            <span className="sr-only">{set.is_pinned ? 'Unpin' : 'Pin'}</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex flex-wrap gap-2">
        {set.difficulty !== null && (
          <Badge variant="secondary">{difficultyLabel(set.difficulty)}</Badge>
        )}
        <Badge variant="outline" className="text-xs">
          <BookOpenIcon className="size-3" />
          {langName(set.source_lang_id, languages)}
          {set.target_lang_id != null ? ` → ${langName(set.target_lang_id, languages)}` : ''}
        </Badge>
        <Badge variant="outline">{set.status}</Badge>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <LayersIcon className="size-3" />
          {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
        </span>
      </CardContent>
    </Card>
  );
}

interface CreatedTabProps {
  onCreateClick: () => void;
}

function CreatedTab({ onCreateClick }: CreatedTabProps) {
  const [page, setPage] = useState(1);
  const skip = (page - 1) * PAGE_SIZE;
  const { data, isLoading, isError, error } = useCreatedSets(skip, PAGE_SIZE);
  const { data: languages = [] } = useAllLanguages();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);
  const [filterLangId, setFilterLangId] = useState<number | null>(activeLanguageId);

  useEffect(() => {
    setFilterLangId(activeLanguageId);
    setPage(1);
  }, [activeLanguageId]);

  const uniqueLangIds = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.data.map((s) => s.source_lang_id))];
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (filterLangId == null) return data.data;
    return data.data.filter((s) => s.source_lang_id === filterLangId);
  }, [data, filterLangId]);

  function handleFilterChange(id: number | null) {
    setFilterLangId(id);
    setPage(1);
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <LibraryCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Empty>
        <EmptyHeader>
          <EmptyTitle>Failed to load sets</EmptyTitle>
          <EmptyDescription>{error.message}</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <PlusIcon />
        </EmptyMedia>
        <EmptyHeader>
          <EmptyTitle>No sets yet</EmptyTitle>
          <EmptyDescription>Create your first vocabulary set to get started.</EmptyDescription>
        </EmptyHeader>
        <Button onClick={onCreateClick}>
          <PlusIcon />
          Create Set
        </Button>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <LangFilterBar
        langIds={uniqueLangIds}
        languages={languages}
        value={filterLangId}
        onChange={handleFilterChange}
      />

      {filtered.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No sets for this language</EmptyTitle>
            <EmptyDescription>Try a different filter or create a new set.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((set) => (
              <CreatedSetCard key={set.id} set={set} languages={languages} />
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
        </div>
      )}
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function SetsListView() {
  const [editorOpen, setEditorOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const navigate = useNavigate();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);
  const { data: libraryData } = useMyLibrary(0, 1);
  const libraryEmpty = libraryData?.total === 0;
  const practiceAllDisabled = !activeLanguageId || libraryEmpty;

  function handlePracticeAll() {
    navigate(`/practice?all=true&lang=${activeLanguageId}`);
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">My Sets</h1>
          <p className="text-sm text-muted-foreground">Manage your vocabulary sets and library.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handlePracticeAll}
            disabled={practiceAllDisabled}
            title={!activeLanguageId ? 'Select a learning language first' : libraryEmpty ? 'Add sets to your library first' : undefined}
          >
            <PlayIcon />
            Practice All
          </Button>
          <Button variant="outline" onClick={() => setImportOpen(true)}>
            <DownloadIcon />
            Import from Anki
          </Button>
          <Button onClick={() => setEditorOpen(true)}>
            <PlusIcon />
            Create Set
          </Button>
        </div>
      </div>

      <Tabs defaultValue="library">
        <TabsList>
          <TabsTrigger value="library">Library</TabsTrigger>
          <TabsTrigger value="created">Created by Me</TabsTrigger>
        </TabsList>

        <TabsContent value="library" className="mt-4">
          <LibraryTab />
        </TabsContent>

        <TabsContent value="created" className="mt-4">
          <CreatedTab onCreateClick={() => setEditorOpen(true)} />
        </TabsContent>
      </Tabs>

      <SetEditor open={editorOpen} onOpenChange={setEditorOpen} />
      <AnkiImportModal open={importOpen} onOpenChange={setImportOpen} />
    </div>
  );
}
