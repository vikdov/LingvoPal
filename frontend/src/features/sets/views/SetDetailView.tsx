import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  PlusIcon,
  PencilIcon,
  Trash2Icon,
  CopyIcon,
  BookmarkPlusIcon,
  BookmarkMinusIcon,
  LayersIcon,
  BookOpenIcon,
  SearchIcon,
  UserIcon,
  FlagIcon,
  SendIcon,
  ClockIcon,
  CheckCircleIcon,
  StarIcon,
  PlayIcon,
  AlertCircleIcon,
  XCircleIcon,
  Volume2Icon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty';
import { PaginationBar } from '@/components/ui/pagination-bar';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuthStore } from '@/features/auth';
import { useAllLanguages } from '@/features/languages';
import {
  useSet,
  useSetItems,
  useAddToLibrary,
  useRemoveFromLibrary,
  useForkSet,
  useDeleteSet,
  useRemoveItem,
  useTouchSet,
  useMyItems,
  usePublicItems,
  useAddExistingItemToSet,
  useSubmitSetForReview,
  useIsInLibrary,
  useLatestSetModeration,
  useSubmitItemForReview,
} from '../hooks/useSetsQuery';
import { SubmitReviewDialog } from '../components/SubmitReviewDialog';
import { SetEditor } from '../components/SetEditor';
import { ItemEditModal } from '../components/ItemEditModal';
import { ItemViewModal } from '../components/ItemViewModal';
import { ReportDialog } from '../components/ReportDialog';
import { SetStatsPanel } from '@/features/stats/components/SetStatsPanel';
import type { SetResponse, ItemDetailResponse, ItemSummaryResponse } from '../types/sets.types';
import { langName, difficultyLabel } from '../utils/formatters';

type PageSize = 20 | 50 | 100;

// ── FindAndAddDialog ──────────────────────────────────────────────────────────

interface FindAndAddDialogProps {
  setId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function FindAndAddDialog({ setId, open, onOpenChange }: FindAndAddDialogProps) {
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState<'mine' | 'public'>('mine');
  const { data: languages = [] } = useAllLanguages();
  const addItem = useAddExistingItemToSet();

  const { data: myData, isFetching: myFetching } = useMyItems(0, 20, query || undefined);
  const { data: publicData, isFetching: publicFetching } = usePublicItems({
    query: query || undefined,
    skip: 0,
    limit: 20,
  });

  const myItems = myData?.data ?? [];
  const publicItems = publicData?.data ?? [];
  function handleAdd(itemId: number, term: string) {
    addItem.mutate(
      { setId, itemId },
      {
        onSuccess: () => toast.success(`"${term}" added to set.`),
        onError: (err) => toast.error(err.message),
      },
    );
  }

  function renderItem(item: ItemDetailResponse | ItemSummaryResponse) {
    return (
      <div key={item.id} className="flex items-center justify-between gap-3 rounded-md border px-3 py-2">
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-sm">{item.term}</p>
          {item.context && (
            <p className="truncate text-xs text-muted-foreground italic">{item.context}</p>
          )}
          <div className="mt-1 flex gap-1">
            <Badge variant="outline" className="text-xs">{langName(item.language_id, languages)}</Badge>
            {item.part_of_speech && <Badge variant="outline" className="text-xs">{item.part_of_speech}</Badge>}
          </div>
        </div>
        <Button
          size="sm"
          variant="outline"
          disabled={addItem.isPending}
          onClick={() => handleAdd(item.id, item.term)}
        >
          <PlusIcon className="size-3.5" />
          Add
        </Button>
      </div>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[672px] max-w-[calc(100vw-2rem)] sm:max-w-[672px]">
        <DialogHeader>
          <DialogTitle>Find & Add Expression</DialogTitle>
        </DialogHeader>

        <div className="relative">
          <SearchIcon className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Search expressions…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>

        <Tabs value={tab} onValueChange={(v) => setTab(v as 'mine' | 'public')}>
          <TabsList className="w-full">
            <TabsTrigger value="mine" className="flex-1">My Expressions</TabsTrigger>
            <TabsTrigger value="public" className="flex-1">Public</TabsTrigger>
          </TabsList>

          <TabsContent value="mine" className="mt-3 flex flex-col gap-2 max-h-96 overflow-y-auto">
            {myFetching && <p className="text-sm text-muted-foreground text-center py-4">Searching…</p>}
            {!myFetching && myItems.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">No expressions found.</p>
            )}
            {myItems.map(renderItem)}
          </TabsContent>

          <TabsContent value="public" className="mt-3 flex flex-col gap-2 max-h-96 overflow-y-auto">
            {publicFetching && <p className="text-sm text-muted-foreground text-center py-4">Searching…</p>}
            {!publicFetching && publicItems.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">No expressions found.</p>
            )}
            {publicItems.map(renderItem)}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
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
  userId: number | null;
  onEdit: (item: ItemDetailResponse) => void;
  onView: (item: ItemDetailResponse) => void;
}

function ItemCard({ item, setId, isOwner, userId, onEdit, onView }: ItemCardProps) {
  const removeItem = useRemoveItem();
  const [reportOpen, setReportOpen] = useState(false);
  const canReport = !isOwner && item.creator_id !== userId && item.status !== 'draft';

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
      className="group overflow-hidden transition-shadow cursor-pointer hover:shadow-md"
      onClick={() => isOwner ? onEdit(item) : onView(item)}
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
          <div className="flex items-center gap-0.5 shrink-0">
            {canReport && (
              <Button
                size="icon-sm"
                variant="ghost"
                className="opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity text-muted-foreground/50 hover:text-destructive"
                onClick={(e) => { e.stopPropagation(); setReportOpen(true); }}
              >
                <FlagIcon className="size-3.5" />
                <span className="sr-only">Report expression</span>
              </Button>
            )}
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
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        {(item.part_of_speech || item.difficulty !== null || (isOwner && item.status === 'draft')) && (
          <div className="flex flex-wrap gap-2">
            {isOwner && item.status === 'draft' && (
              <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-400">
                Draft
              </Badge>
            )}
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
          <button
            type="button"
            onClick={() => { new Audio(item.audio_url!).play().catch(() => {}); }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50 hover:bg-muted transition-colors text-sm text-muted-foreground hover:text-foreground w-fit"
          >
            <Volume2Icon className="size-3.5 shrink-0" />
            Play audio
          </button>
        )}
      </CardContent>

      {canReport && (
        <ReportDialog
          targetId={item.id}
          targetType="item"
          open={reportOpen}
          onOpenChange={setReportOpen}
        />
      )}
    </Card>
  );
}

// ── Set status banner (owner-only) ────────────────────────────────────────────

interface SetStatusBannerProps {
  set: SetResponse;
}

function SetStatusBanner({ set }: SetStatusBannerProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const submitSet = useSubmitSetForReview();
  const { data: latestModeration } = useLatestSetModeration(set.id);

  function handleSubmit(feedback?: string) {
    submitSet.mutate(
      { setId: set.id, feedback },
      {
        onSuccess: () => {
          toast.success('Set submitted for review. It\'s now visible to the community.');
          setDialogOpen(false);
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }

  const wasRejected = latestModeration?.status === 'rejected';

  if (set.status === 'draft') {
    return (
      <>
        {wasRejected && latestModeration?.resolution_feedback && (
          <div className="flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
            <XCircleIcon className="size-4 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium">Rejected by moderator</p>
              <p className="text-xs opacity-75 mt-0.5">{latestModeration.resolution_feedback}</p>
            </div>
          </div>
        )}
        <div className="flex items-center justify-between gap-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/50 dark:bg-amber-950/30">
          <div className="flex items-center gap-2.5 text-amber-800 dark:text-amber-300">
            <SendIcon className="size-4 shrink-0" />
            <div>
              <p className="text-sm font-medium">This set is private</p>
              <p className="text-xs opacity-75">
                {wasRejected
                  ? 'Address the feedback above, then resubmit for review.'
                  : 'Submit for community review to share it publicly.'}
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0 border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100 dark:border-amber-800 dark:bg-transparent dark:text-amber-300 dark:hover:bg-amber-950/50"
            onClick={() => setDialogOpen(true)}
          >
            {wasRejected ? 'Resubmit' : 'Submit for Review'}
          </Button>
        </div>
        <SubmitReviewDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          targetLabel={set.title}
          isPending={submitSet.isPending}
          onSubmit={handleSubmit}
        />
      </>
    );
  }

  if (set.status === 'community') {
    return (
      <div className="flex items-center gap-2.5 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-blue-800 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-300">
        <ClockIcon className="size-4 shrink-0" />
        <div>
          <p className="text-sm font-medium">Under review</p>
          <p className="text-xs opacity-75">Visible to the community while pending moderation.</p>
        </div>
      </div>
    );
  }

  if (set.status === 'approved') {
    return (
      <div className="flex items-center gap-2.5 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-800 dark:border-green-900/50 dark:bg-green-950/30 dark:text-green-300">
        <CheckCircleIcon className="size-4 shrink-0" />
        <div>
          <p className="text-sm font-medium">Published</p>
          <p className="text-xs opacity-75">Approved and visible to the community.</p>
        </div>
      </div>
    );
  }

  if (set.status === 'official') {
    return (
      <div className="flex items-center gap-2.5 rounded-lg border border-violet-200 bg-violet-50 px-4 py-3 text-violet-800 dark:border-violet-900/50 dark:bg-violet-950/30 dark:text-violet-300">
        <StarIcon className="size-4 shrink-0" />
        <div>
          <p className="text-sm font-medium">Official set</p>
          <p className="text-xs opacity-75">Verified and curated by LingvoPal.</p>
        </div>
      </div>
    );
  }

  return null;
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
      {set.item_count > 0 && (
        <Button size="sm" onClick={() => navigate(`/practice?setId=${set.id}`)}>
          <PlayIcon className="size-3.5" />
          Practice
        </Button>
      )}
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
  const { data: inLibrary = false, isLoading: libraryLoading } = useIsInLibrary(set.id);

  function handleLibraryToggle() {
    if (inLibrary) {
      removeFromLibrary.mutate(set.id, {
        onSuccess: () => toast.success('Removed from library.'),
        onError: (err) => toast.error(err.message),
      });
    } else {
      addToLibrary.mutate(set.id, {
        onSuccess: () => toast.success('Added to library.'),
        onError: (err) => toast.error(err.message),
      });
    }
  }

  function handleFork() {
    forkSet.mutate(set.id, {
      onSuccess: (forked) => {
        toast.success('Duplicated to your sets.');
        navigate(`/sets/${forked.id}`);
      },
      onError: (err) => toast.error(err.message),
    });
  }

  const libraryPending = addToLibrary.isPending || removeFromLibrary.isPending || libraryLoading;

  return (
    <>
      {inLibrary && set.item_count > 0 && (
        <Button size="sm" onClick={() => navigate(`/practice?setId=${set.id}`)}>
          <PlayIcon className="size-4" />
          Practice
        </Button>
      )}
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
        <CopyIcon className="size-4" />
        Duplicate
      </Button>
    </>
  );
}

// ── Bulk submit drafts ────────────────────────────────────────────────────────

interface BulkSubmitDraftsButtonProps {
  draftItems: ItemDetailResponse[];
}

function BulkSubmitDraftsButton({ draftItems }: BulkSubmitDraftsButtonProps) {
  const submitItem = useSubmitItemForReview();
  const [pending, setPending] = useState(false);

  async function handleBulkSubmit() {
    if (!window.confirm(`Submit all ${draftItems.length} draft expressions for review?`)) return;
    setPending(true);
    let ok = 0;
    let fail = 0;
    for (const item of draftItems) {
      try {
        await new Promise<void>((resolve, reject) => {
          submitItem.mutate(
            { itemId: item.id },
            { onSuccess: () => resolve(), onError: reject },
          );
        });
        ok++;
      } catch {
        fail++;
      }
    }
    setPending(false);
    if (fail === 0) toast.success(`${ok} expression${ok !== 1 ? 's' : ''} submitted for review.`);
    else toast.warning(`${ok} submitted, ${fail} failed.`);
  }

  return (
    <Button
      size="sm"
      variant="outline"
      className="border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100 dark:border-amber-800 dark:bg-transparent dark:text-amber-300 dark:hover:bg-amber-950/50"
      onClick={handleBulkSubmit}
      disabled={pending || submitItem.isPending}
    >
      <AlertCircleIcon className="size-3.5" />
      Submit {draftItems.length} Drafts
    </Button>
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
  const [findAndAddOpen, setFindAndAddOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ItemDetailResponse | undefined>(undefined);
  const [viewingItem, setViewingItem] = useState<ItemDetailResponse | null>(null);

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
  const draftItems = isOwner ? items.filter((e) => e.item.status === 'draft').map((e) => e.item) : [];

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
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <LayersIcon className="size-3" />
            {set.item_count} {set.item_count === 1 ? 'item' : 'items'}
          </span>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <BookOpenIcon className="size-3" />
            {langName(set.source_lang_id, languages)}{set.target_lang_id != null ? ` → ${langName(set.target_lang_id, languages)}` : ''}
          </span>
          {set.creator_username && !isOwner && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <UserIcon className="size-3" />
              {set.creator_username}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {isOwner ? (
            <>
              <OwnerActions set={set} onEdit={() => setEditorOpen(true)} />
              <Button size="sm" onClick={handleAddItem}>
                <PlusIcon className="size-3.5" />
                New
              </Button>
              <Button size="sm" variant="outline" onClick={() => setFindAndAddOpen(true)}>
                <SearchIcon className="size-3.5" />
                Find & Add
              </Button>
            </>
          ) : (
            <ViewerActions set={set} />
          )}
        </div>
      </div>

      <Separator />

      {/* Status banner — owner only */}
      {isOwner && <SetStatusBanner set={set} />}

      {/* Contextual stats panel — only shown when user has practice data */}
      <SetStatsPanel setId={setId} />

      {/* Items list */}
      <div ref={itemsSectionRef} className="flex flex-col gap-4 scroll-mt-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-lg font-medium">
            Items{total > 0 ? ` (${total})` : ''}
          </h2>
          {isOwner && draftItems.length > 1 && (
            <BulkSubmitDraftsButton draftItems={draftItems} />
          )}
        </div>

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
                  userId={user?.id ?? null}
                  onEdit={handleEditItem}
                  onView={setViewingItem}
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

      <FindAndAddDialog
        setId={setId}
        open={findAndAddOpen}
        onOpenChange={setFindAndAddOpen}
      />

      {viewingItem && (
        <ItemViewModal
          item={viewingItem}
          open={!!viewingItem}
          onOpenChange={(open) => { if (!open) setViewingItem(null); }}
        />
      )}
    </div>
  );
}
