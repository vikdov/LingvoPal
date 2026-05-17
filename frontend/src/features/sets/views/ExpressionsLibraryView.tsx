import { useState } from 'react';
import { toast } from 'sonner';
import {
  Trash2Icon,
  PencilIcon,
  LayersIcon,
  BookOpenIcon,
  PlusIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty';
import { PaginationBar } from '@/components/ui/pagination-bar';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAllLanguages } from '@/features/languages';
import type { LanguageRef } from '@/features/languages';
import { useMyItems, useDeleteItem, useMyLibrary, useMySets } from '../hooks/useSetsQuery';
import { ItemEditModal } from '../components/ItemEditModal';
import { LibraryEntryCard } from './SetsListView';
import type { ItemDetailResponse } from '../types/sets.types';
import { langName, difficultyLabel } from '../utils/formatters';

type PageSize = 20 | 50 | 100;

// ── Skeletons ─────────────────────────────────────────────────────────────────

function ExpressionCardSkeleton() {
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

// ── Expression card ───────────────────────────────────────────────────────────

interface ExpressionCardProps {
  item: ItemDetailResponse;
  languages: LanguageRef[];
  onEdit: (item: ItemDetailResponse) => void;
  onDelete: (item: ItemDetailResponse) => void;
}

function ExpressionCard({ item, languages, onEdit, onDelete }: ExpressionCardProps) {
  return (
    <Card
      size="sm"
      className="cursor-pointer overflow-hidden transition-shadow hover:shadow-md"
      onClick={() => onEdit(item)}
    >
      {item.image_url && (
        <div className="aspect-video w-full overflow-hidden">
          <img src={item.image_url} alt={item.term} className="h-full w-full object-cover" />
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
          <div className="flex shrink-0 gap-1">
            <Button
              size="icon-sm"
              variant="ghost"
              onClick={(e) => { e.stopPropagation(); onEdit(item); }}
            >
              <PencilIcon className="size-3.5" />
              <span className="sr-only">Edit</span>
            </Button>
            <Button
              size="icon-sm"
              variant="ghost"
              className="text-destructive hover:text-destructive"
              onClick={(e) => { e.stopPropagation(); onDelete(item); }}
            >
              <Trash2Icon className="size-3.5" />
              <span className="sr-only">Delete</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="outline" className="text-xs">{langName(item.language_id, languages)}</Badge>
          {item.part_of_speech && <Badge variant="outline">{item.part_of_speech}</Badge>}
          {item.difficulty !== null && <Badge variant="secondary">{difficultyLabel(item.difficulty)}</Badge>}
          <Badge variant={item.status === 'draft' ? 'secondary' : 'default'} className="text-xs">
            {item.status}
          </Badge>
        </div>

        {item.translations.length > 0 && (
          <div className="flex flex-col gap-1">
            <p className="text-xs font-medium text-muted-foreground">Translations</p>
            {item.translations.slice(0, 2).map((t) => (
              <div key={t.id} className="rounded-md bg-muted/50 px-2.5 py-1.5">
                <span className="text-sm font-medium">{t.term_trans}</span>
                <span className="ml-1.5 text-xs text-muted-foreground">
                  {langName(t.language_id, languages)}
                </span>
              </div>
            ))}
            {item.translations.length > 2 && (
              <p className="text-xs text-muted-foreground">+{item.translations.length - 2} more</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── New expression card ───────────────────────────────────────────────────────

function NewExpressionCard({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="group flex aspect-square w-full self-center flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-muted-foreground/25 bg-transparent text-muted-foreground/50 transition-all hover:border-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="flex size-10 items-center justify-center rounded-full border-2 border-dashed border-current transition-transform group-hover:scale-110">
        <PlusIcon className="size-5" />
      </div>
      <span className="text-sm font-medium">New expression</span>
    </button>
  );
}

// ── Set picker dialog ─────────────────────────────────────────────────────────

interface SetPickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sets: Array<{ id: number; title: string }>;
  onConfirm: (setId: number) => void;
}

function SetPickerDialog({ open, onOpenChange, sets, onConfirm }: SetPickerDialogProps) {
  const [selectedSetId, setSelectedSetId] = useState<string>(
    sets.length > 0 ? String(sets[0].id) : ''
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add to which set?</DialogTitle>
        </DialogHeader>
        <Select value={selectedSetId} onValueChange={setSelectedSetId}>
          <SelectTrigger>
            <SelectValue placeholder="Choose a set…" />
          </SelectTrigger>
          <SelectContent>
            {sets.map((s) => (
              <SelectItem key={s.id} value={String(s.id)}>
                {s.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            disabled={!selectedSetId}
            onClick={() => { onConfirm(Number(selectedSetId)); onOpenChange(false); }}
          >
            Continue
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── My Expressions tab ────────────────────────────────────────────────────────

function MyExpressionsTab({ languages }: { languages: LanguageRef[] }) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<PageSize>(20);
  const skip = (page - 1) * pageSize;

  const { data, isLoading, isFetching } = useMyItems(skip, pageSize);
  const deleteItem = useDeleteItem();
  const { data: setsData } = useMySets(0, 100);
  const sets = setsData?.data ?? [];

  const [editingItem, setEditingItem] = useState<ItemDetailResponse | undefined>(undefined);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editModalSetId, setEditModalSetId] = useState<number>(0);
  const [setPickerOpen, setSetPickerOpen] = useState(false);

  const items = data?.data ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 0;

  function handleNewExpression() {
    if (sets.length === 0) {
      toast.error('Create a set first before adding expressions.');
      return;
    }
    if (sets.length === 1) {
      setEditingItem(undefined);
      setEditModalSetId(sets[0].id);
      setEditModalOpen(true);
    } else {
      setSetPickerOpen(true);
    }
  }

  function handleSetPicked(setId: number) {
    setEditingItem(undefined);
    setEditModalSetId(setId);
    setEditModalOpen(true);
  }

  function handleEdit(item: ItemDetailResponse) {
    setEditingItem(item);
    setEditModalSetId(0);
    setEditModalOpen(true);
  }

  function handleDelete(item: ItemDetailResponse) {
    const shared = item.status !== 'draft';
    const msg = shared
      ? `"${item.term}" is used by other learners. It will be released to the community (no longer yours). Continue?`
      : `Delete "${item.term}"? This cannot be undone.`;
    if (!window.confirm(msg)) return;
    deleteItem.mutate(item.id, {
      onSuccess: () => toast.success(shared ? 'Expression released to community.' : 'Expression deleted.'),
      onError: (err) => toast.error(err.message),
    });
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => <ExpressionCardSkeleton key={i} />)}
      </div>
    );
  }

  return (
    <>
      <div className={`grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 transition-opacity duration-150 ${isFetching ? 'opacity-60' : 'opacity-100'}`}>
        <NewExpressionCard onClick={handleNewExpression} />
        {items.length === 0 && !isLoading && (
          <div className="col-span-full flex flex-col items-center justify-center gap-1 py-12 text-center text-muted-foreground">
            <LayersIcon className="size-8 opacity-30" />
            <p className="text-sm">No expressions yet. Create your first one.</p>
          </div>
        )}
        {items.map((item) => (
          <ExpressionCard
            key={item.id}
            item={item}
            languages={languages}
            onEdit={handleEdit}
            onDelete={handleDelete}
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
        onPageChange={setPage}
        onPageSizeChange={(s) => { setPageSize(s as PageSize); setPage(1); }}
      />

      <SetPickerDialog
        open={setPickerOpen}
        onOpenChange={setSetPickerOpen}
        sets={sets}
        onConfirm={handleSetPicked}
      />

      <ItemEditModal
        open={editModalOpen}
        onOpenChange={setEditModalOpen}
        setId={editModalSetId}
        item={editingItem}
      />
    </>
  );
}

// ── In My Sets tab ────────────────────────────────────────────────────────────

function InMySetsTab({ languages }: { languages: LanguageRef[] }) {
  const { data, isLoading } = useMyLibrary(0, 50);
  const entries = data?.data ?? [];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => <ExpressionCardSkeleton key={i} />)}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon"><BookOpenIcon className="size-4" /></EmptyMedia>
        <EmptyHeader>
          <EmptyTitle>No sets in library</EmptyTitle>
          <EmptyDescription>Add sets to your library to see them here.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {entries.map((entry) => (
        <LibraryEntryCard key={entry.set_id} entry={entry} languages={languages} />
      ))}
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function ExpressionsLibraryView() {
  const { data: languages = [] } = useAllLanguages();

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">My Expressions</h1>
        <p className="text-sm text-muted-foreground">
          Manage all vocabulary you&apos;ve created or collected.
        </p>
      </div>

      <Tabs defaultValue="mine">
        <TabsList>
          <TabsTrigger value="mine">Created by Me</TabsTrigger>
          <TabsTrigger value="library">In My Sets</TabsTrigger>
        </TabsList>

        <TabsContent value="mine" className="mt-6">
          <MyExpressionsTab languages={languages} />
        </TabsContent>

        <TabsContent value="library" className="mt-6">
          <InMySetsTab languages={languages} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
