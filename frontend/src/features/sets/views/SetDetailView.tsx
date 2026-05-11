import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  PlusIcon,
  PencilIcon,
  Trash2Icon,
  GitForkIcon,
  BookmarkPlusIcon,
  BookmarkMinusIcon,
  LayersIcon,
  BookOpenIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty';
import { PaginationBar } from '@/components/ui/pagination-bar';
import { useAuthStore } from '@/features/auth';
import { useAllLanguages } from '@/features/languages';
import type { LanguageRef } from '@/features/languages';
import {
  useSet,
  useSetItems,
  useAddToLibrary,
  useRemoveFromLibrary,
  useForkSet,
  useDeleteSet,
  useRemoveItem,
  useTouchSet,
} from '../hooks/useSetsQuery';
import { SetEditor } from '../components/SetEditor';
import { ItemEditModal } from '../components/ItemEditModal';
import { SetStatsPanel } from '@/features/stats/components/SetStatsPanel';
import type { SetResponse, ItemDetailResponse } from '../types/sets.types';

type PageSize = 20 | 50 | 100;

function langName(id: number | null | undefined, languages: LanguageRef[]): string {
  if (id == null) return '';
  return languages.find((l) => l.id === id)?.name ?? String(id);
}

function difficultyLabel(difficulty: number | null): string {
  if (difficulty === null) return 'Any';
  const labels = ['', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Native'];
  return labels[difficulty] ?? String(difficulty);
}

// ── Skeletons ─────────────────────────────────────────────────────────────────

function SetHeaderSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-4 w-3/4" />
      <div className="flex gap-2">
        <Skeleton className="h-6 w-12" />
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-6 w-20" />
      </div>
    </div>
  );
}

function ItemCardSkeleton() {
  return (
    <Card size="sm">
      <CardHeader>
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-4 w-2/3" />
      </CardHeader>
      <CardContent className="flex gap-2">
        <Skeleton className="h-5 w-10" />
        <Skeleton className="h-5 w-14" />
      </CardContent>
    </Card>
  );
}

// ── Item card ─────────────────────────────────────────────────────────────────

interface ItemCardProps {
  item: ItemDetailResponse;
  setId: number;
  isOwner: boolean;
  onEdit: (item: ItemDetailResponse) => void;
}

function ItemCard({ item, setId, isOwner, onEdit }: ItemCardProps) {
  const removeItem = useRemoveItem();

  function handleRemove() {
    if (!window.confirm(`Remove "${item.term}" from this set? The expression stays in the vocabulary and can still appear in discovery.`)) return;
    removeItem.mutate(
      { setId, itemId: item.id },
      {
        onSuccess: () => toast.success('Item removed.'),
        onError: (err) => toast.error(err.message),
      },
    );
  }

  return (
    <Card
      size="sm"
      className={`overflow-hidden transition-shadow ${isOwner ? 'cursor-pointer hover:shadow-md' : ''}`}
      onClick={isOwner ? () => onEdit(item) : undefined}
    >
      {item.image_url && (
        <div className="aspect-video w-full overflow-hidden">
          <img
            src={item.image_url}
            alt={item.term}
            className="h-full w-full object-cover"
          />
        </div>
      )}

      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <CardTitle className="text-base">{item.term}</CardTitle>
            {item.lemma && item.lemma !== item.term && (
              <p className="text-xs text-muted-foreground">({item.lemma})</p>
            )}
            {item.context && (
              <CardDescription className="mt-0.5 line-clamp-2 italic">
                &ldquo;{item.context}&rdquo;
              </CardDescription>
            )}
          </div>
          {isOwner && (
            <Button
              size="icon-sm"
              variant="ghost"
              className="shrink-0 text-destructive hover:text-destructive"
              onClick={(e) => { e.stopPropagation(); handleRemove(); }}
              disabled={removeItem.isPending}
            >
              <Trash2Icon className="size-3.5" />
              <span className="sr-only">Remove from set</span>
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        {(item.part_of_speech || item.difficulty !== null) && (
          <div className="flex flex-wrap gap-2">
            {item.part_of_speech && (
              <Badge variant="outline">{item.part_of_speech}</Badge>
            )}
            {item.difficulty !== null && (
              <Badge variant="secondary">{difficultyLabel(item.difficulty)}</Badge>
            )}
          </div>
        )}

        {item.translations.length > 0 && (
          <div className="flex flex-col gap-1">
            <p className="text-xs font-medium text-muted-foreground">Translations</p>
            <div className="flex flex-col gap-1">
              {item.translations.map((t) => (
                <div key={t.id} className="rounded-md bg-muted/50 px-2.5 py-1.5">
                  <span className="text-sm font-medium">{t.term_trans}</span>
                  {t.context_trans && (
                    <span className="ml-2 text-xs text-muted-foreground italic">
                      &ldquo;{t.context_trans}&rdquo;
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {item.audio_url && (
          <audio controls className="w-full" src={item.audio_url} />
        )}
      </CardContent>
    </Card>
  );
}

// ── Set header actions ────────────────────────────────────────────────────────

interface OwnerActionsProps {
  set: SetResponse;
  onEdit: () => void;
}

function OwnerActions({ set, onEdit }: OwnerActionsProps) {
  const navigate = useNavigate();
  const deleteSet = useDeleteSet();

  function handleDelete() {
    if (!window.confirm(`Delete "${set.title}"? This cannot be undone.`)) return;
    deleteSet.mutate(set.id, {
      onSuccess: () => {
        toast.success('Set deleted.');
        navigate('/sets');
      },
      onError: (err) => toast.error(err.message),
    });
  }

  return (
    <>
      <Button size="sm" variant="outline" onClick={onEdit}>
        <PencilIcon className="size-3.5" />
        Edit Set
      </Button>
      <Button
        size="sm"
        variant="ghost"
        className="text-destructive hover:text-destructive"
        onClick={handleDelete}
        disabled={deleteSet.isPending}
      >
        <Trash2Icon className="size-3.5" />
        Delete
      </Button>
    </>
  );
}

interface ViewerActionsProps {
  set: SetResponse;
}

function ViewerActions({ set }: ViewerActionsProps) {
  const navigate = useNavigate();
  const addToLibrary = useAddToLibrary();
  const removeFromLibrary = useRemoveFromLibrary();
  const forkSet = useForkSet();
  const [inLibrary, setInLibrary] = useState(false);

  function handleLibraryToggle() {
    if (inLibrary) {
      removeFromLibrary.mutate(set.id, {
        onSuccess: () => {
          toast.success('Removed from library.');
          setInLibrary(false);
        },
        onError: (err) => toast.error(err.message),
      });
    } else {
      addToLibrary.mutate(set.id, {
        onSuccess: () => {
          toast.success('Added to library.');
          setInLibrary(true);
        },
        onError: (err) => toast.error(err.message),
      });
    }
  }

  function handleFork() {
    forkSet.mutate(set.id, {
      onSuccess: (forked) => {
        toast.success('Set forked successfully.');
        navigate(`/sets/${forked.id}`);
      },
      onError: (err) => toast.error(err.message),
    });
  }

  const libraryPending = addToLibrary.isPending || removeFromLibrary.isPending;

  return (
    <>
      <Button
        size="sm"
        variant={inLibrary ? 'outline' : 'default'}
        onClick={handleLibraryToggle}
        disabled={libraryPending}
      >
        {inLibrary ? (
          <>
            <BookmarkMinusIcon className="size-4" />
            Remove from Library
          </>
        ) : (
          <>
            <BookmarkPlusIcon className="size-4" />
            Add to Library
          </>
        )}
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={handleFork}
        disabled={forkSet.isPending}
      >
        <GitForkIcon className="size-4" />
        Fork
      </Button>
    </>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function SetDetailView() {
  const { setId: setIdParam } = useParams<{ setId: string }>();
  const setId = Number(setIdParam ?? 0);
  const user = useAuthStore((s) => s.user);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<PageSize>(20);
  const skip = (page - 1) * pageSize;

  const itemsSectionRef = useRef<HTMLDivElement>(null);

  const { data: set, isLoading: setLoading, isError: setError } = useSet(setId);
  const { data: itemsData, isLoading: itemsLoading, isFetching } = useSetItems(setId, skip, pageSize);
  const { data: languages = [] } = useAllLanguages();
  const touchSet = useTouchSet();

  // Record that the user opened this set (fire-and-forget)
  useEffect(() => {
    if (setId > 0) touchSet.mutate(setId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setId]);

  const [editorOpen, setEditorOpen] = useState(false);
  const [itemModalOpen, setItemModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ItemDetailResponse | undefined>(undefined);

  const isOwner = !!user && !!set && set.creator_id === user.id;

  // Scroll items section into view on page/pageSize change (skip initial mount)
  const isFirstRender = useRef(true);
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    itemsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [page, pageSize]);

  function handlePageChange(newPage: number) {
    setPage(newPage);
  }

  function handlePageSizeChange(newSize: number) {
    setPageSize(newSize as PageSize);
    setPage(1);
  }

  function handleAddItem() {
    setEditingItem(undefined);
    setItemModalOpen(true);
  }

  function handleEditItem(item: ItemDetailResponse) {
    setEditingItem(item);
    setItemModalOpen(true);
  }

  if (setLoading) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <SetHeaderSkeleton />
        <Separator />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <ItemCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (setError || !set) {
    return (
      <div className="p-6">
        <Empty>
          <EmptyHeader>
            <EmptyTitle>Set not found</EmptyTitle>
            <EmptyDescription>
              This set does not exist or you don&apos;t have access to it.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      </div>
    );
  }

  const items = itemsData?.data ?? [];
  const total = itemsData?.total ?? 0;
  const pages = itemsData?.pages ?? 0;

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Set header */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">{set.title}</h1>
          {set.description && (
            <p className="text-sm text-muted-foreground">{set.description}</p>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {set.difficulty !== null && (
            <Badge variant="secondary">{difficultyLabel(set.difficulty)}</Badge>
          )}
          <Badge variant="outline">{set.status}</Badge>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <LayersIcon className="size-3" />
            {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
          </span>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <BookOpenIcon className="size-3" />
            {langName(set.source_lang_id, languages)}{set.target_lang_id != null ? ` → ${langName(set.target_lang_id, languages)}` : ''}
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {isOwner ? (
            <>
              <OwnerActions set={set} onEdit={() => setEditorOpen(true)} />
              <Button size="sm" onClick={handleAddItem}>
                <PlusIcon className="size-3.5" />
                Add Item
              </Button>
            </>
          ) : (
            <ViewerActions set={set} />
          )}
        </div>
      </div>

      <Separator />

      {/* Contextual stats panel — only shown when user has practice data */}
      <SetStatsPanel setId={setId} />

      {/* Items list */}
      <div ref={itemsSectionRef} className="flex flex-col gap-4 scroll-mt-4">
        <h2 className="text-lg font-medium">
          Items{total > 0 ? ` (${total})` : ''}
        </h2>

        {itemsLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: Math.min(pageSize, 6) }).map((_, i) => (
              <ItemCardSkeleton key={i} />
            ))}
          </div>
        )}

        {!itemsLoading && items.length === 0 && (
          <Empty>
            <EmptyMedia variant="icon">
              <LayersIcon className="size-4" />
            </EmptyMedia>
            <EmptyHeader>
              <EmptyTitle>No items yet</EmptyTitle>
              <EmptyDescription>
                {isOwner
                  ? 'Add vocabulary items to this set to start learning.'
                  : 'This set has no items yet.'}
              </EmptyDescription>
            </EmptyHeader>
            {isOwner && (
              <Button onClick={handleAddItem}>
                <PlusIcon className="size-3.5" />
                Add Item
              </Button>
            )}
          </Empty>
        )}

        {!itemsLoading && items.length > 0 && (
          <>
            <div
              className={`grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 transition-opacity duration-150 ${isFetching ? 'opacity-60' : 'opacity-100'}`}
            >
              {items.map((entry) => (
                <ItemCard
                  key={entry.item_id}
                  item={entry.item}
                  setId={setId}
                  isOwner={isOwner}
                  onEdit={handleEditItem}
                />
              ))}
            </div>

            <PaginationBar
              page={page}
              pages={pages}
              pageSize={pageSize}
              total={total}
              skip={skip}
              isFetching={isFetching}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          </>
        )}
      </div>

      {/* Dialogs */}
      <SetEditor
        open={editorOpen}
        onOpenChange={setEditorOpen}
        set={set}
      />

      <ItemEditModal
        open={itemModalOpen}
        onOpenChange={setItemModalOpen}
        setId={setId}
        item={editingItem}
        defaultLanguageId={set.source_lang_id}
        defaultTranslationLanguageId={set.target_lang_id}
      />
    </div>
  );
}
