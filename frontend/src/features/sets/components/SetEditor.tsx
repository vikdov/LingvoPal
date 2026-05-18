import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { InfoIcon } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAllLanguages, useLanguageStore } from '@/features/languages';
import { useCreateSet, useUpdateSet } from '../hooks/useSetsQuery';
import type { SetResponse } from '../types/sets.types';

interface SetEditorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When provided, the dialog is in edit mode */
  set?: SetResponse;
  /** Called after a successful create/update with the resulting set */
  onSuccess?: (set: SetResponse) => void;
}

const DIFFICULTY_OPTIONS = [
  { value: '1', label: 'A1 – Beginner' },
  { value: '2', label: 'A2 – Elementary' },
  { value: '3', label: 'B1 – Intermediate' },
  { value: '4', label: 'B2 – Upper-Intermediate' },
  { value: '5', label: 'C1 – Advanced' },
  { value: '6', label: 'C2 – Proficiency' },
  { value: '7', label: 'Native' },
];

const TARGET_NONE = '__none__';

export function SetEditor({ open, onOpenChange, set, onSuccess }: SetEditorProps) {
  const { data: languages = [] } = useAllLanguages();
  const activeLanguageId = useLanguageStore((s) => s.activeLanguageId);
  const isEditing = !!set;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [difficulty, setDifficulty] = useState<string>('');
  const [sourceLangId, setSourceLangId] = useState<string>('');
  const [targetLangId, setTargetLangId] = useState<string>('');

  const createSet = useCreateSet();
  const updateSet = useUpdateSet();

  const isPending = createSet.isPending || updateSet.isPending;

  // When editing, source lang is locked if the set has items
  const sourceLangLocked = isEditing && (set?.item_count ?? 0) > 0;

  // Populate fields when opening
  useEffect(() => {
    if (set) {
      setTitle(set.title);
      setDescription(set.description ?? '');
      setDifficulty(set.difficulty != null ? String(set.difficulty) : '');
      setSourceLangId(String(set.source_lang_id));
      setTargetLangId(set.target_lang_id != null ? String(set.target_lang_id) : TARGET_NONE);
    } else {
      setTitle('');
      setDescription('');
      setDifficulty('');
      setSourceLangId(activeLanguageId ? String(activeLanguageId) : '');
      setTargetLangId(TARGET_NONE);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [set, open]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!title.trim()) {
      toast.error('Title is required.');
      return;
    }

    if (!isEditing && !sourceLangId) {
      toast.error('Source language is required.');
      return;
    }

    if (isEditing) {
      const resolvedTargetLang =
        targetLangId === TARGET_NONE ? null : Number(targetLangId);
      const resolvedSourceLang = sourceLangLocked
        ? undefined
        : sourceLangId
          ? Number(sourceLangId)
          : undefined;

      updateSet.mutate(
        {
          setId: set.id,
          body: {
            title: title.trim(),
            description: description.trim() || undefined,
            difficulty: difficulty ? Number(difficulty) : undefined,
            ...(resolvedSourceLang !== undefined && { source_lang_id: resolvedSourceLang }),
            target_lang_id: resolvedTargetLang,
          },
        },
        {
          onSuccess: (updated) => {
            toast.success('Set updated.');
            onSuccess?.(updated);
            onOpenChange(false);
          },
          onError: (err) => toast.error(err.message),
        },
      );
    } else {
      const resolvedTargetLang =
        targetLangId === TARGET_NONE ? null : Number(targetLangId) || undefined;

      createSet.mutate(
        {
          title: title.trim(),
          description: description.trim() || undefined,
          difficulty: difficulty ? Number(difficulty) : undefined,
          source_lang_id: Number(sourceLangId),
          target_lang_id: resolvedTargetLang,
        },
        {
          onSuccess: (created) => {
            toast.success('Set created.');
            onSuccess?.(created);
            onOpenChange(false);
          },
          onError: (err) => toast.error(err.message),
        },
      );
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Set' : 'Create Set'}</DialogTitle>
        </DialogHeader>

        <form id="set-editor-form" onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Title */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="set-title">Title *</Label>
            <Input
              id="set-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Business English Vocabulary"
              disabled={isPending}
              autoFocus
            />
          </div>

          {/* Description */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="set-description">Description</Label>
            <Textarea
              id="set-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description…"
              rows={2}
              disabled={isPending}
            />
          </div>

          {/* Difficulty — edit only, meaningless before items exist */}
          {isEditing && (
            <div className="flex flex-col gap-1.5">
              <Label>Difficulty</Label>
              <Select value={difficulty} onValueChange={setDifficulty} disabled={isPending}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Any level" />
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
          )}

          {/* Language fields — always shown in create, shown in edit too */}
          <div className="grid grid-cols-2 gap-3">
            {/* Source language */}
            <div className="flex flex-col gap-1.5">
              <Label>Learning {!isEditing && '*'}</Label>
              <Select
                value={sourceLangId}
                onValueChange={setSourceLangId}
                disabled={isPending || sourceLangLocked}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select…" />
                </SelectTrigger>
                <SelectContent>
                  {languages.map((l) => (
                    <SelectItem key={l.id} value={String(l.id)}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {sourceLangLocked && (
                <p className="flex items-center gap-1 text-xs text-muted-foreground">
                  <InfoIcon className="size-3 shrink-0" />
                  Locked — set has {set!.item_count} item{set!.item_count !== 1 ? 's' : ''}
                </p>
              )}
            </div>

            {/* Target language */}
            <div className="flex flex-col gap-1.5">
              <Label>Translate to</Label>
              <Select
                value={targetLangId}
                onValueChange={setTargetLangId}
                disabled={isPending}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={TARGET_NONE}>
                    <span className="text-muted-foreground">None</span>
                  </SelectItem>
                  {languages.map((l) => (
                    <SelectItem key={l.id} value={String(l.id)}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </form>

        <DialogFooter showCloseButton>
          <Button type="submit" form="set-editor-form" disabled={isPending}>
            {isPending ? 'Saving…' : isEditing ? 'Save Changes' : 'Create Set'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
