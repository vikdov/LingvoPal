import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { PlusIcon, BookmarkIcon, BookmarkCheckIcon, BookOpenIcon, LayersIcon, DownloadIcon, PlayIcon, SearchIcon, LibraryIcon, MoreHorizontalIcon, Trash2Icon, ClockIcon } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAllLanguages } from '@/features/languages';
import { useLanguageStore } from '@/features/languages/store/language.store';
import type { LanguageRef } from '@/features/languages';
import { Link } from 'react-router-dom';
import { useMyLibrary, useCreatedSets, useRemoveFromLibrary, usePinSet, useTouchSet } from '../hooks/useSetsQuery';
import { langAccentColor } from '../components/SetCover';
import { SetEditor } from '../components/SetEditor';
import { AnkiImportModal } from '../components/AnkiImportModal';
import type { SetLibraryEntry, CreatedSetSummaryResponse } from '../types/sets.types';
import { langName, difficultyLabel } from '../utils/formatters';
import { cn } from '@/lib/utils';

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return 'Never opened';
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

function withOpacity(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
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
    <div className="flex items-center h-8">
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
    </div>
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
      <CardContent className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Skeleton className="h-5 w-12" />
          <Skeleton className="h-5 w-16" />
        </div>
        <Skeleton className="h-8 w-20" />
      </CardContent>
    </Card>
  );
}

export interface LibraryEntryCardProps {
  entry: SetLibraryEntry;
  languages: LanguageRef[];
}

export function LibraryEntryCard({ entry, languages }: LibraryEntryCardProps) {
  const navigate = useNavigate();
  const removeFromLibrary = useRemoveFromLibrary();
  const pinSet = usePinSet();
  const touchSet = useTouchSet();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const { set } = entry;

  function handleRemoveConfirmed() {
    removeFromLibrary.mutate(entry.set_id, {
      onSuccess: () => { setConfirmOpen(false); toast.success('Removed from library.'); },
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
    <>
      <Card
        className="h-full min-h-36 border-l-4 cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5 hover:ring-foreground/20 justify-between"
        style={{ borderLeftColor: withOpacity(accentColor, 0.65) }}
        onClick={() => { touchSet.mutate(entry.set_id); navigate(`/sets/${entry.set_id}`); }}
      >
        <CardHeader className="gap-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="line-clamp-2 flex-1">{set.title}</CardTitle>
            <div className="flex items-center gap-0.5 shrink-0">
              <Button
                size="icon-sm"
                variant="ghost"
                onClick={(e) => { e.stopPropagation(); handlePinToggle(); }}
                disabled={pinSet.isPending}
                title={entry.is_pinned ? 'Unpin' : 'Save'}
              >
                {entry.is_pinned ? (
                  <BookmarkCheckIcon className="size-4 text-primary" />
                ) : (
                  <BookmarkIcon className="size-4" />
                )}
                <span className="sr-only">{entry.is_pinned ? 'Unpin' : 'Save'}</span>
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    size="icon-sm"
                    variant="ghost"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreHorizontalIcon className="size-4" />
                    <span className="sr-only">More options</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenuItem
                    className="text-destructive focus:text-destructive"
                    onSelect={() => setConfirmOpen(true)}
                  >
                    <Trash2Icon className="size-4" />
                    Remove from library
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-foreground/65">
            <span className="flex items-center gap-1">
              <LayersIcon className="size-3" />
              {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
            </span>
            {entry.due_count > 0 && (
              <>
                <span aria-hidden>·</span>
                <span className="text-primary font-medium">{entry.due_count} due</span>
              </>
            )}
            <span aria-hidden>·</span>
            <span className="flex items-center gap-1">
              <ClockIcon className="size-3" />
              {relativeTime(entry.last_opened_at)}
            </span>
          </div>
        </CardHeader>

        <CardContent>
          <div className="flex items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {set.difficulty !== null && (
                <Badge variant="secondary">{difficultyLabel(set.difficulty)}</Badge>
              )}
              <Badge variant="outline" className="text-xs">
                <BookOpenIcon className="size-3" />
                {langName(set.source_lang_id, languages)}
                {set.target_lang_id != null ? ` → ${langName(set.target_lang_id, languages)}` : ''}
              </Badge>
            </div>
            <Button
              size="sm"
              variant={entry.due_count > 0 ? 'default' : 'outline'}
              className={cn('shrink-0', entry.due_count === 0 ? 'border-foreground/25 text-foreground' : undefined)}
              onClick={(e) => { e.stopPropagation(); touchSet.mutate(entry.set_id); navigate(`/practice?setId=${entry.set_id}`); }}
              disabled={set.item_count === 0}
              title={set.item_count === 0 ? 'No items to study' : undefined}
            >
              {entry.due_count > 0 ? `Study (${entry.due_count} due)` : 'Review'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove from library</DialogTitle>
            <DialogDescription>
              Remove &ldquo;{set.title}&rdquo; from your library? Your progress is preserved.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>Cancel</Button>
            <Button
              variant="destructive"
              onClick={handleRemoveConfirmed}
              disabled={removeFromLibrary.isPending}
            >
              {removeFromLibrary.isPending ? 'Removing…' : 'Remove'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function LibraryTab() {
  const { data, isLoading, isError, error } = useMyLibrary(0, 200);
  const { data: languages = [] } = useAllLanguages();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);
  const [filterLangId, setFilterLangId] = useState<number | null>(activeLanguageId);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setFilterLangId(activeLanguageId);
  }, [activeLanguageId]);

  const uniqueLangIds = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.data.map((e) => e.set.source_lang_id))];
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    let result = filterLangId == null ? data.data : data.data.filter((e) => e.set.source_lang_id === filterLangId);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter((e) => e.set.title.toLowerCase().includes(q));
    }
    return result;
  }, [data, filterLangId, search]);

  function handleFilterChange(id: number | null) {
    setFilterLangId(id);
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
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <SearchIcon className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search sets…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-8 text-sm"
          />
        </div>
        <LangFilterBar
          langIds={uniqueLangIds}
          languages={languages}
          value={filterLangId}
          onChange={handleFilterChange}
        />
      </div>

      {filtered.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>{search ? 'No matches' : 'No sets for this language'}</EmptyTitle>
            <EmptyDescription>
              {search ? 'Try a different search term.' : 'Try a different filter or add more sets to your library.'}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((entry) => (
            <LibraryEntryCard key={entry.set_id} entry={entry} languages={languages} />
          ))}
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
      className="h-full min-h-36 border-l-4 cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5 hover:ring-foreground/20 justify-between"
      style={{ borderLeftColor: withOpacity(accentColor, 0.65) }}
      onClick={() => { touchSet.mutate(set.id); navigate(`/sets/${set.id}`); }}
    >
      <CardHeader className="gap-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2 flex-1">{set.title}</CardTitle>
          <Button
            size="icon-sm"
            variant="ghost"
            onClick={(e) => { e.stopPropagation(); handlePinToggle(); }}
            disabled={pinSet.isPending}
            title={set.is_pinned ? 'Unpin' : 'Save'}
          >
            {set.is_pinned ? (
              <BookmarkCheckIcon className="size-4 text-primary" />
            ) : (
              <BookmarkIcon className="size-4" />
            )}
            <span className="sr-only">{set.is_pinned ? 'Unpin' : 'Save'}</span>
          </Button>
        </div>
        <div className="flex items-center gap-1 text-sm text-foreground/65">
          <LayersIcon className="size-3" />
          {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
        </div>
      </CardHeader>

      <CardContent>
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-wrap gap-2">
            {set.difficulty !== null && (
              <Badge variant="secondary">{difficultyLabel(set.difficulty)}</Badge>
            )}
            <Badge variant="outline" className="text-xs">
              <BookOpenIcon className="size-3" />
              {langName(set.source_lang_id, languages)}
              {set.target_lang_id != null ? ` → ${langName(set.target_lang_id, languages)}` : ''}
            </Badge>
            <Badge variant="outline">{set.status}</Badge>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0 border-foreground/25 text-foreground"
            onClick={(e) => { e.stopPropagation(); touchSet.mutate(set.id); navigate(`/practice?setId=${set.id}`); }}
            disabled={set.item_count === 0}
            title={set.item_count === 0 ? 'No items to study' : undefined}
          >
            Study
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface CreatedTabProps {
  onCreateClick: () => void;
}

function CreatedTab({ onCreateClick }: CreatedTabProps) {
  const { data, isLoading, isError, error } = useCreatedSets(0, 200);
  const { data: languages = [] } = useAllLanguages();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);
  const [filterLangId, setFilterLangId] = useState<number | null>(activeLanguageId);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setFilterLangId(activeLanguageId);
  }, [activeLanguageId]);

  const uniqueLangIds = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.data.map((s) => s.source_lang_id))];
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    let result = filterLangId == null ? data.data : data.data.filter((s) => s.source_lang_id === filterLangId);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter((s) => s.title.toLowerCase().includes(q));
    }
    return result;
  }, [data, filterLangId, search]);

  function handleFilterChange(id: number | null) {
    setFilterLangId(id);
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
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <SearchIcon className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search sets…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-8 text-sm"
          />
        </div>
        <LangFilterBar
          langIds={uniqueLangIds}
          languages={languages}
          value={filterLangId}
          onChange={handleFilterChange}
        />
      </div>

      {filtered.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>{search ? 'No matches' : 'No sets for this language'}</EmptyTitle>
            <EmptyDescription>
              {search ? 'Try a different search term.' : 'Try a different filter or create a new set.'}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((set) => (
            <CreatedSetCard key={set.id} set={set} languages={languages} />
          ))}
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
            variant="ghost"
            onClick={handlePracticeAll}
            disabled={practiceAllDisabled}
            title={!activeLanguageId ? 'Select a learning language first' : libraryEmpty ? 'Add sets to your library first' : undefined}
          >
            <PlayIcon />
            Practice All
          </Button>
          <Button variant="outline" asChild>
            <Link to="/words">
              <LibraryIcon />
              My Expressions
            </Link>
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
