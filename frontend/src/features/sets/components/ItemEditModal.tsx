import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import {
  PlusIcon,
  PencilIcon,
  Trash2Icon,
  CheckIcon,
  XIcon,
  ImageIcon,
  MicIcon,
  Loader2Icon,
  Volume2Icon,
  SearchIcon,
  ChevronDownIcon,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
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
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useAllLanguages } from '@/features/languages';
import {
  useCreateItem,
  useUpdateItem,
  useUploadItemImage,
  useUploadItemAudio,
  useCreateTranslation,
  useUpdateTranslation,
  useDeleteTranslation,
  useItemSynonyms,
  useSetSynonyms,
  useSynonymSuggestions,
  setKeys,
} from '../hooks/useSetsQuery';
import { setsApi } from '../api/sets.api';
import type {
  ItemDetailResponse,
  TranslationResponse,
  PartOfSpeech,
} from '../types/sets.types';
import type { LanguageRef } from '@/features/languages';

// ── Constants ─────────────────────────────────────────────────────────────────

const POS_OPTIONS: { value: PartOfSpeech; label: string }[] = [
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

// ── Types ─────────────────────────────────────────────────────────────────────

interface PendingTranslation {
  _key: string;
  language_id: number;
  term_trans: string;
  context_trans: string;
}

// Replace standalone _ with the actual word (e.g. "She _ home" → "She went home")
function resolveContext(ctx: string, word: string): string {
  const resolved = ctx.replace(/\b_\b/g, word);
  return resolved.charAt(0).toUpperCase() + resolved.slice(1);
}

// ── SectionHeading ────────────────────────────────────────────────────────────

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </p>
  );
}

// ── ImageUploadZone ───────────────────────────────────────────────────────────

interface ImageUploadZoneProps {
  previewUrl: string | null;
  isPending: boolean;
  canClear: boolean;
  onSelect: (file: File) => void;
  onClear: () => void;
}

function ImageUploadZone({ previewUrl, isPending, canClear, onSelect, onClear }: ImageUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const zoneRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  function pickImageFile(files: FileList | null): File | null {
    if (!files) return null;
    for (const f of Array.from(files)) {
      if (f.type.startsWith('image/')) return f;
    }
    return null;
  }

  function handlePaste(e: React.ClipboardEvent) {
    e.preventDefault();
    if (isPending) return;
    const file = pickImageFile(e.clipboardData.files);
    if (file) onSelect(file);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    if (!isDragging) setIsDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    if (!zoneRef.current?.contains(e.relatedTarget as Node)) setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    if (isPending) return;
    const file = pickImageFile(e.dataTransfer.files);
    if (file) onSelect(file);
  }

  return (
    <div className="flex flex-col gap-2">
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onSelect(file);
          e.target.value = '';
        }}
      />
      <div
        ref={zoneRef}
        onClick={() => !isPending && inputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'relative flex min-h-[160px] w-full items-center justify-center overflow-hidden rounded-lg border-2 border-dashed border-border bg-muted/40 transition-colors',
          !previewUrl && 'cursor-pointer hover:border-primary/50 hover:bg-muted/60',
          isDragging && 'border-primary bg-primary/5',
          isPending && 'cursor-not-allowed opacity-60',
        )}
      >
        {/* Transparent contenteditable overlay so right-click → Paste is available */}
        <div
          contentEditable
          suppressContentEditableWarning
          onPaste={handlePaste}
          onClick={(e) => { e.stopPropagation(); if (!isPending) inputRef.current?.click(); }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className="absolute inset-0 z-10 cursor-pointer opacity-0"
          aria-hidden="true"
        />

        {previewUrl ? (
          <img src={previewUrl} alt="Preview" className="h-full w-full object-cover" />
        ) : (
          <div className="flex flex-col items-center gap-2 text-muted-foreground">
            <ImageIcon className="size-8 opacity-40" />
            <span className="text-xs">{isDragging ? 'Drop image here' : 'Click, paste, or drag image'}</span>
          </div>
        )}
        {isPending && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/60">
            <Loader2Icon className="size-5 animate-spin text-muted-foreground" />
          </div>
        )}
      </div>

      {previewUrl && (
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="flex-1"
            onClick={() => inputRef.current?.click()}
            disabled={isPending}
          >
            Replace
          </Button>
          {canClear && (
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              className="text-destructive hover:text-destructive"
              onClick={onClear}
              disabled={isPending}
            >
              <Trash2Icon className="size-3.5" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// ── AudioUploadRow ────────────────────────────────────────────────────────────

interface AudioUploadRowProps {
  audioUrl: string | null;
  pendingFileName: string | null;
  isPending: boolean;
  onSelect: (file: File) => void;
  onClearPending: () => void;
}

function AudioUploadRow({ audioUrl, pendingFileName, isPending, onSelect, onClearPending }: AudioUploadRowProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex flex-col gap-2">
      <input
        ref={inputRef}
        type="file"
        accept="audio/mpeg,audio/ogg,audio/wav,audio/mp4,audio/webm"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onSelect(file);
          e.target.value = '';
        }}
      />

      {audioUrl ? (
        <div className="flex flex-col gap-2 rounded-lg border border-border bg-muted/30 p-3">
          <div className="flex items-center gap-2">
            <Volume2Icon className="size-4 shrink-0 text-muted-foreground" />
            <audio controls className="h-8 flex-1 min-w-0" src={audioUrl} />
          </div>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => inputRef.current?.click()}
            disabled={isPending}
          >
            {isPending ? <Loader2Icon className="size-3.5 animate-spin" /> : <MicIcon className="size-3.5" />}
            {isPending ? 'Uploading…' : 'Replace Audio'}
          </Button>
        </div>
      ) : pendingFileName ? (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
          <MicIcon className="size-4 shrink-0 text-muted-foreground" />
          <span className="flex-1 truncate text-sm text-muted-foreground">{pendingFileName}</span>
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            className="shrink-0 text-destructive hover:text-destructive"
            onClick={onClearPending}
          >
            <XIcon className="size-3.5" />
          </Button>
        </div>
      ) : (
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => inputRef.current?.click()}
          disabled={isPending}
          className="w-full"
        >
          {isPending ? <Loader2Icon className="size-3.5 animate-spin" /> : <MicIcon className="size-3.5" />}
          {isPending ? 'Uploading…' : 'Upload Audio'}
        </Button>
      )}
    </div>
  );
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function ContextDisplay({ text }: { text: string }) {
  const html = text.replace(/\{([^}]+)\}/g, '<strong class="font-semibold not-italic">$1</strong>');
  return <span className="mt-0.5 text-xs text-muted-foreground" dangerouslySetInnerHTML={{ __html: html }} />;
}

interface ContextEditProps {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}

function ContextEdit({ value, onChange, disabled }: ContextEditProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  function markSelection() {
    const el = ref.current;
    if (!el) return;
    const { selectionStart: s, selectionEnd: e, value: v } = el;
    if (s === null || e === null) return;
    const next = s === e ? v.slice(0, s) + '{}' + v.slice(e) : v.slice(0, s) + '{' + v.slice(s, e) + '}' + v.slice(e);
    onChange(next);
    requestAnimationFrame(() => {
      el.focus();
      const cur = s === e ? s + 1 : e + 2;
      el.setSelectionRange(cur, cur);
    });
  }

  const preview = value.includes('{')
    ? value.replace(/\{([^}]+)\}/g, '<mark class="bg-primary/20 text-primary font-semibold rounded px-0.5">$1</mark>')
    : '';

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Context sentence</span>
        <Button type="button" size="sm" variant="ghost" onClick={markSelection} disabled={disabled} className="h-6 px-2 text-xs">
          Mark selected
        </Button>
      </div>
      <Textarea
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="e.g. Hello {everyone} today…"
        disabled={disabled}
        rows={2}
        className="resize-none overflow-hidden text-sm"
      />
      {preview && (
        <p className="rounded bg-muted/60 px-2 py-1 text-xs text-muted-foreground">
          <span className="mr-1 font-medium text-muted-foreground/60">Preview:</span>
          <span dangerouslySetInnerHTML={{ __html: preview }} />
        </p>
      )}
    </div>
  );
}

// ── TranslationRow — edit mode (immediate mutations) ──────────────────────────

interface TranslationRowProps {
  translation: TranslationResponse;
  itemId: number;
  setId: number;
  languages: LanguageRef[];
}

function TranslationRow({ translation, itemId, setId, languages }: TranslationRowProps) {
  const [editing, setEditing] = useState(false);
  const [termTrans, setTermTrans] = useState(translation.term_trans);
  const [contextTrans, setContextTrans] = useState(translation.context_trans ?? '');
  const updateTranslation = useUpdateTranslation(setId);
  const deleteTranslation = useDeleteTranslation(setId);

  const langName =
    languages.find((l) => l.id === translation.language_id)?.name ??
    `Lang ${translation.language_id}`;

  function handleSave() {
    if (!termTrans.trim()) {
      toast.error('Translation is required.');
      return;
    }
    updateTranslation.mutate(
      {
        itemId,
        translationId: translation.id,
        body: { term_trans: termTrans.trim(), context_trans: contextTrans.trim() || null },
      },
      {
        onSuccess: () => {
          toast.success('Translation updated.');
          setEditing(false);
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }

  function handleDelete() {
    if (!window.confirm('Delete this translation?')) return;
    deleteTranslation.mutate(
      { itemId, translationId: translation.id },
      {
        onSuccess: () => toast.success('Translation deleted.'),
        onError: (err) => toast.error(err.message),
      },
    );
  }

  if (editing) {
    return (
      <div className="flex flex-col gap-2 rounded-lg border border-border bg-muted/30 p-3">
        <Input
          value={termTrans}
          onChange={(e) => setTermTrans(e.target.value)}
          placeholder="Translation"
          disabled={updateTranslation.isPending}
        />
        <ContextEdit value={contextTrans} onChange={setContextTrans} disabled={updateTranslation.isPending} />
        <div className="flex gap-2">
          <Button size="sm" type="button" onClick={handleSave} disabled={updateTranslation.isPending}>
            <CheckIcon className="size-3.5" />
            {updateTranslation.isPending ? 'Saving…' : 'Save'}
          </Button>
          <Button
            size="sm"
            type="button"
            variant="ghost"
            onClick={() => {
              setEditing(false);
              setTermTrans(translation.term_trans);
              setContextTrans(translation.context_trans ?? '');
            }}
          >
            <XIcon className="size-3.5" />
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-between gap-2 rounded-lg border border-border p-3">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{translation.term_trans}</p>
        {translation.context_trans && (
          <ContextDisplay text={translation.context_trans} />
        )}
        <Badge variant="outline" className="mt-1.5 text-xs">{langName}</Badge>
      </div>
      <div className="flex shrink-0 gap-1">
        <Button size="icon-sm" variant="ghost" onClick={() => setEditing(true)}>
          <PencilIcon className="size-3.5" />
        </Button>
        <Button
          size="icon-sm"
          variant="ghost"
          className="text-destructive hover:text-destructive"
          onClick={handleDelete}
          disabled={deleteTranslation.isPending}
        >
          <Trash2Icon className="size-3.5" />
        </Button>
      </div>
    </div>
  );
}

// ── PendingTranslationRow — create mode (local state) ─────────────────────────

interface PendingTranslationRowProps {
  pt: PendingTranslation;
  languages: LanguageRef[];
  onDelete: (key: string) => void;
  onEdit: (key: string, updated: Omit<PendingTranslation, '_key'>) => void;
}

function PendingTranslationRow({ pt, languages, onDelete, onEdit }: PendingTranslationRowProps) {
  const [editing, setEditing] = useState(false);
  const [termTrans, setTermTrans] = useState(pt.term_trans);
  const [contextTrans, setContextTrans] = useState(pt.context_trans);
  const langName = languages.find((l) => l.id === pt.language_id)?.name ?? `Lang ${pt.language_id}`;

  function handleSave() {
    if (!termTrans.trim()) {
      toast.error('Translation is required.');
      return;
    }
    onEdit(pt._key, { language_id: pt.language_id, term_trans: termTrans.trim(), context_trans: contextTrans.trim() });
    setEditing(false);
  }

  if (editing) {
    return (
      <div className="flex flex-col gap-2 rounded-lg border border-border bg-muted/30 p-3">
        <Input
          value={termTrans}
          onChange={(e) => setTermTrans(e.target.value)}
          placeholder="Translation"
          autoFocus
        />
        <ContextEdit value={contextTrans} onChange={setContextTrans} />
        <div className="flex gap-2">
          <Button size="sm" type="button" onClick={handleSave}>
            <CheckIcon className="size-3.5" />
            Save
          </Button>
          <Button
            size="sm"
            type="button"
            variant="ghost"
            onClick={() => {
              setEditing(false);
              setTermTrans(pt.term_trans);
              setContextTrans(pt.context_trans);
            }}
          >
            <XIcon className="size-3.5" />
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-between gap-2 rounded-lg border border-border p-3">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{pt.term_trans}</p>
        {pt.context_trans && (
          <ContextDisplay text={pt.context_trans} />
        )}
        <Badge variant="outline" className="mt-1.5 text-xs">{langName}</Badge>
      </div>
      <div className="flex shrink-0 gap-1">
        <Button size="icon-sm" type="button" variant="ghost" onClick={() => setEditing(true)}>
          <PencilIcon className="size-3.5" />
        </Button>
        <Button
          size="icon-sm"
          type="button"
          variant="ghost"
          className="text-destructive hover:text-destructive"
          onClick={() => onDelete(pt._key)}
        >
          <Trash2Icon className="size-3.5" />
        </Button>
      </div>
    </div>
  );
}

// ── AddTranslationForm ────────────────────────────────────────────────────────

interface AddTranslationFormProps {
  languages: LanguageRef[];
  existingLanguageIds: number[];
  setId: number;
  defaultLanguageId?: number | null;
  // Edit mode: itemId provided, mutations fire immediately
  itemId?: number;
  // Create mode: onAdd collects into local state
  onAdd?: (pt: Omit<PendingTranslation, '_key'>) => void;
}

function AddTranslationForm({
  languages,
  existingLanguageIds,
  setId,
  defaultLanguageId,
  itemId,
  onAdd,
}: AddTranslationFormProps) {
  const [open, setOpen] = useState(false);
  const [langId, setLangId] = useState(() =>
    defaultLanguageId && !existingLanguageIds.includes(defaultLanguageId)
      ? String(defaultLanguageId)
      : ''
  );
  const [termTrans, setTermTrans] = useState('');
  const [contextTrans, setContextTrans] = useState('');
  const createTranslation = useCreateTranslation(setId);

  const available = languages.filter((l) => !existingLanguageIds.includes(l.id));

  function reset() {
    setOpen(false);
    setLangId(
      defaultLanguageId && !existingLanguageIds.includes(defaultLanguageId)
        ? String(defaultLanguageId)
        : ''
    );
    setTermTrans('');
    setContextTrans('');
  }

  function handleAdd() {
    if (!langId || !termTrans.trim()) {
      toast.error('Language and translation are required.');
      return;
    }

    if (onAdd) {
      onAdd({ language_id: Number(langId), term_trans: termTrans.trim(), context_trans: contextTrans.trim() });
      reset();
      return;
    }

    if (itemId != null) {
      createTranslation.mutate(
        { itemId, body: { language_id: Number(langId), term_trans: termTrans.trim(), context_trans: contextTrans.trim() || null } },
        { onSuccess: () => { toast.success('Translation added.'); reset(); }, onError: (err) => toast.error(err.message) },
      );
    }
  }

  if (!open) {
    return (
      <Button type="button" size="sm" variant="outline" disabled={available.length === 0} onClick={() => setOpen(true)}>
        <PlusIcon className="size-3.5" />
        {available.length === 0 ? 'All languages covered' : 'Add Translation'}
      </Button>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3 flex flex-col gap-2">
      <Select value={langId} onValueChange={setLangId} disabled={createTranslation.isPending}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Language…" />
        </SelectTrigger>
        <SelectContent>
          {available.map((l) => (
            <SelectItem key={l.id} value={String(l.id)}>{l.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Input
        value={termTrans}
        onChange={(e) => setTermTrans(e.target.value)}
        placeholder="Translation *"
        disabled={createTranslation.isPending}
        autoFocus
      />

      <ContextEdit value={contextTrans} onChange={setContextTrans} disabled={createTranslation.isPending} />

      <div className="flex justify-end gap-1.5">
        <Button size="sm" type="button" variant="ghost" onClick={reset} disabled={createTranslation.isPending}>
          Cancel
        </Button>
        <Button size="sm" type="button" onClick={handleAdd} disabled={createTranslation.isPending}>
          {createTranslation.isPending ? 'Adding…' : 'Add'}
        </Button>
      </div>
    </div>
  );
}

// ── SynonymsSection ───────────────────────────────────────────────────────────

interface SynonymsSectionProps {
  languageId: number | null;
  // Edit mode: itemId provided, mutations fire immediately
  itemId?: number;
  // Create mode: terms managed by parent
  pendingTerms?: string[];
  onChangePending?: (terms: string[]) => void;
}

function SynonymsSection({ itemId, languageId, pendingTerms, onChangePending }: SynonymsSectionProps) {
  const isEditMode = itemId != null;
  const [input, setInput] = useState('');
  const [debouncedInput, setDebouncedInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: savedTerms = [], isLoading } = useItemSynonyms(itemId);
  const setSynonyms = useSetSynonyms();

  useEffect(() => {
    const t = setTimeout(() => setDebouncedInput(input), 250);
    return () => clearTimeout(t);
  }, [input]);

  const { data: suggestions = [] } = useSynonymSuggestions(languageId, debouncedInput);

  const activeTerms: string[] = isEditMode ? savedTerms : (pendingTerms ?? []);
  const termSet = new Set(activeTerms.map((t) => t.toLowerCase()));
  const filteredSuggestions = suggestions.filter((s) => !termSet.has(s.toLowerCase()));

  function addTerm(term: string) {
    const t = term.trim();
    if (!t || termSet.has(t.toLowerCase())) return;
    const next = [...activeTerms, t];
    if (isEditMode) {
      setSynonyms.mutate(
        { itemId: itemId!, terms: next },
        { onSuccess: () => toast.success('Synonyms updated.'), onError: (err) => toast.error(err.message) },
      );
    } else {
      onChangePending?.(next);
    }
    setInput('');
  }

  function removeTerm(term: string) {
    const next = activeTerms.filter((t) => t !== term);
    if (isEditMode) {
      setSynonyms.mutate(
        { itemId: itemId!, terms: next },
        { onError: (err) => toast.error(err.message) },
      );
    } else {
      onChangePending?.(next);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTerm(input);
    } else if (e.key === 'Backspace' && !input && activeTerms.length > 0) {
      removeTerm(activeTerms[activeTerms.length - 1]);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      {isEditMode && isLoading ? (
        <p className="text-xs text-muted-foreground">Loading…</p>
      ) : activeTerms.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {activeTerms.map((term) => (
            <span
              key={term}
              className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/50 px-2.5 py-1 text-xs font-medium"
            >
              {term}
              <button
                type="button"
                onClick={() => removeTerm(term)}
                disabled={isEditMode && setSynonyms.isPending}
                className="ml-0.5 rounded-full text-muted-foreground hover:text-destructive"
                aria-label={`Remove ${term}`}
              >
                <XIcon className="size-3" />
              </button>
            </span>
          ))}
        </div>
      ) : null}

      <div className="relative w-full min-w-0">
        <div className="flex w-full min-w-0 items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 focus-within:ring-1 focus-within:ring-ring">
          <SearchIcon className="size-3.5 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={languageId ? 'Type synonym, Enter to add…' : 'Select language first'}
            disabled={!languageId}
            className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed"
          />
        </div>

        {debouncedInput && filteredSuggestions.length > 0 && (
          <div className="absolute left-0 right-0 top-full z-20 mt-1 flex max-h-36 flex-col gap-0.5 overflow-y-auto rounded-lg border border-border bg-popover p-1 shadow-md">
            {filteredSuggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => addTerm(s)}
                className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-sm hover:bg-muted/50"
              >
                <PlusIcon className="size-3 shrink-0 text-muted-foreground" />
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Enter or comma to add · Backspace to remove last
      </p>
    </div>
  );
}

// ── Main modal ────────────────────────────────────────────────────────────────

interface ItemEditModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  setId: number;
  item?: ItemDetailResponse;
  defaultLanguageId?: number;
  defaultTranslationLanguageId?: number | null;
  onSuccess?: () => void;
}

export function ItemEditModal({
  open,
  onOpenChange,
  setId,
  item,
  defaultLanguageId,
  defaultTranslationLanguageId,
  onSuccess,
}: ItemEditModalProps) {
  const isEditing = !!item;
  const qc = useQueryClient();
  const { data: languages = [] } = useAllLanguages();

  // Core fields
  const [term, setTerm] = useState('');
  const [context, setContext] = useState('');
  const [lemma, setLemma] = useState('');
  const [partOfSpeech, setPartOfSpeech] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [langId, setLangId] = useState('');

  // Pending media — create mode only (edit mode uploads immediately)
  const [pendingImage, setPendingImage] = useState<File | null>(null);
  const [pendingImageUrl, setPendingImageUrl] = useState<string | null>(null);
  const [pendingAudio, setPendingAudio] = useState<File | null>(null);
  const [pendingAudioName, setPendingAudioName] = useState<string | null>(null);

  // Pending translations + synonyms — create mode only
  const [pendingTranslations, setPendingTranslations] = useState<PendingTranslation[]>([]);
  const [pendingSynonyms, setPendingSynonyms] = useState<string[]>([]);

  const [showAdvanced, setShowAdvanced] = useState(false);

  // Covers the entire create-then-enrich async sequence
  const [isSaving, setIsSaving] = useState(false);

  const createItem = useCreateItem();
  const updateItem = useUpdateItem(setId);
  const uploadImage = useUploadItemImage(setId);
  const uploadAudio = useUploadItemAudio(setId);

  const isPending = isEditing
    ? updateItem.isPending || uploadImage.isPending || uploadAudio.isPending
    : isSaving;

  // Derive object URL from pending image file
  useEffect(() => {
    if (!pendingImage) {
      setPendingImageUrl(null);
      return;
    }
    const url = URL.createObjectURL(pendingImage);
    setPendingImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [pendingImage]);

  // Reset all state when the modal opens or the item changes
  useEffect(() => {
    if (!open) return;
    if (item) {
      setTerm(item.term);
      setContext(item.context ?? '');
      setLemma(item.lemma ?? '');
      setPartOfSpeech(item.part_of_speech ?? '');
      setDifficulty(item.difficulty != null ? String(item.difficulty) : '');
      setLangId(String(item.language_id));
    } else {
      setTerm('');
      setContext('');
      setLemma('');
      setPartOfSpeech('');
      setDifficulty('');
      setLangId(defaultLanguageId ? String(defaultLanguageId) : '');
    }
    setPendingImage(null);
    setPendingAudio(null);
    setPendingAudioName(null);
    setPendingTranslations([]);
    setPendingSynonyms([]);
    setShowAdvanced(false);
  }, [open, item, defaultLanguageId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!term.trim()) {
      toast.error('Term is required.');
      return;
    }

    const pos = partOfSpeech === '_none' ? null : (partOfSpeech as PartOfSpeech) || null;
    const diff = difficulty === '_none' ? null : difficulty ? Number(difficulty) : null;
    const resolvedContext = context.trim() ? resolveContext(context.trim(), term.trim()) : null;

    if (isEditing) {
      updateItem.mutate(
        {
          itemId: item.id,
          body: { term: term.trim(), context: resolvedContext, part_of_speech: pos, difficulty: diff, lemma: lemma.trim() || null },
        },
        {
          onSuccess: () => {
            toast.success('Item updated.');
            onSuccess?.();
            onOpenChange(false);
          },
          onError: (err) => toast.error(err.message),
        },
      );
      return;
    }

    if (!langId) {
      toast.error('Language is required.');
      return;
    }

    setIsSaving(true);
    try {
      const created = await createItem.mutateAsync({
        setId,
        body: {
          term: term.trim(),
          language_id: Number(langId),
          context: resolvedContext || undefined,
          part_of_speech: pos ?? undefined,
          difficulty: diff ?? undefined,
          lemma: lemma.trim() || undefined,
        },
      });

      const enrichments = await Promise.allSettled([
        pendingImage ? setsApi.uploadItemImage(created.id, pendingImage) : Promise.resolve(null),
        pendingAudio ? setsApi.uploadItemAudio(created.id, pendingAudio) : Promise.resolve(null),
        ...pendingTranslations.map((pt) =>
          setsApi.createTranslation(created.id, {
            language_id: pt.language_id,
            term_trans: pt.term_trans,
            context_trans: pt.context_trans || null,
          }),
        ),
        pendingSynonyms.length > 0 ? setsApi.setItemSynonyms(created.id, pendingSynonyms) : Promise.resolve(null),
      ]);

      const failures = enrichments.filter((r) => r.status === 'rejected').length;
      if (failures > 0) {
        toast.warning(`Item created, but ${failures} upload(s) failed.`);
      } else {
        toast.success('Item added.');
      }

      qc.invalidateQueries({ queryKey: setKeys.items(setId) });
      onSuccess?.();
      onOpenChange(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create item.');
    } finally {
      setIsSaving(false);
    }
  }

  function handleImageSelect(file: File) {
    if (!isEditing) {
      setPendingImage(file);
      return;
    }
    uploadImage.mutate(
      { itemId: item!.id, file },
      {
        onSuccess: () => toast.success('Image uploaded.'),
        onError: (err) => toast.error(err.message),
      },
    );
  }

  function handleAudioSelect(file: File) {
    if (!isEditing) {
      setPendingAudio(file);
      setPendingAudioName(file.name);
      return;
    }
    uploadAudio.mutate(
      { itemId: item!.id, file },
      {
        onSuccess: () => toast.success('Audio uploaded.'),
        onError: (err) => toast.error(err.message),
      },
    );
  }

  const imagePreviewUrl = isEditing ? (item?.image_url ?? null) : pendingImageUrl;
  const liveAudioUrl = isEditing ? (item?.audio_url ?? null) : null;
  const existingTranslationLangIds = isEditing
    ? (item?.translations.map((t) => t.language_id) ?? [])
    : pendingTranslations.map((pt) => pt.language_id);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[920px] max-h-[90vh] flex flex-col !p-0 !gap-0 overflow-hidden"
        showCloseButton
      >
        {/* Header */}
        <DialogHeader className="shrink-0 border-b border-border px-6 py-4">
          <DialogTitle className="text-base font-semibold">
            {isEditing ? `Edit "${item.term}"` : 'Add Item'}
          </DialogTitle>
        </DialogHeader>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto">
          <form id="item-edit-form" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 divide-y divide-border md:grid-cols-[1fr_340px] md:divide-x md:divide-y-0">

              {/* ── Left: core fields ─────────────────────────── */}
              <div className="flex flex-col gap-4 p-6">

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="item-term">
                    Expression <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="item-term"
                    value={term}
                    onChange={(e) => setTerm(e.target.value)}
                    placeholder="e.g. walked, went, children"
                    className="h-11 text-base"
                    disabled={isPending}
                    autoFocus
                  />
                  <p className="text-xs text-muted-foreground">Exact form as it appears in the sentence</p>
                </div>

                {!isEditing && (
                  <div className="flex flex-col gap-1.5">
                    <Label>
                      Language <span className="text-destructive">*</span>
                    </Label>
                    <Select value={langId} onValueChange={setLangId} disabled={isPending}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select language…" />
                      </SelectTrigger>
                      <SelectContent>
                        {languages.map((l) => (
                          <SelectItem key={l.id} value={String(l.id)}>
                            {l.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="item-context">Context Sentence</Label>
                  <Textarea
                    id="item-context"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="She _ home… (use _ as placeholder)"
                    rows={3}
                    disabled={isPending}
                  />
                  {context.includes('_') && term.trim() && (
                    <p className="rounded-md bg-muted/60 px-3 py-2 text-sm text-muted-foreground">
                      Preview: <span className="text-foreground">{resolveContext(context, term.trim())}</span>
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => setShowAdvanced((v) => !v)}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors w-fit"
                >
                  <ChevronDownIcon className={cn('size-3.5 transition-transform', showAdvanced && 'rotate-180')} />
                  {showAdvanced ? 'Hide advanced' : 'Advanced fields'}
                </button>

                {showAdvanced && (
                  <>
                    <div className="flex flex-col gap-1.5">
                      <Label htmlFor="item-lemma">Dictionary Form</Label>
                      <Input
                        id="item-lemma"
                        value={lemma}
                        onChange={(e) => setLemma(e.target.value)}
                        placeholder="e.g. go (base form of went)"
                        disabled={isPending}
                      />
                      <p className="text-xs text-muted-foreground">Base/lemma form for grouping and lookup</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex flex-col gap-1.5">
                        <Label>Part of Speech</Label>
                        <Select value={partOfSpeech} onValueChange={setPartOfSpeech} disabled={isPending}>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="None" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="_none">None</SelectItem>
                            {POS_OPTIONS.map((opt) => (
                              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <Label>Difficulty</Label>
                        <Select value={difficulty} onValueChange={setDifficulty} disabled={isPending}>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Any" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="_none">Any</SelectItem>
                            {DIFFICULTY_OPTIONS.map((opt) => (
                              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* ── Right: sticky column with its own scroll ─── */}
              <div className="flex flex-col gap-5 p-5 min-w-0 md:sticky md:top-0 md:self-start md:max-h-[calc(90vh-8rem)] md:overflow-y-auto">

                {/* Media */}
                <div className="flex flex-col gap-2">
                  <SectionHeading>Media</SectionHeading>
                  <ImageUploadZone
                    previewUrl={imagePreviewUrl}
                    isPending={uploadImage.isPending}
                    canClear={!isEditing}
                    onSelect={handleImageSelect}
                    onClear={() => setPendingImage(null)}
                  />
                  <AudioUploadRow
                    audioUrl={liveAudioUrl}
                    pendingFileName={pendingAudioName}
                    isPending={uploadAudio.isPending}
                    onSelect={handleAudioSelect}
                    onClearPending={() => {
                      setPendingAudio(null);
                      setPendingAudioName(null);
                    }}
                  />
                </div>

                <div className="flex flex-col gap-2.5">
                  <SectionHeading>Translations</SectionHeading>

                  {isEditing &&
                    item.translations.map((t) => (
                      <TranslationRow
                        key={t.id}
                        translation={t}
                        itemId={item.id}
                        setId={setId}
                        languages={languages}
                      />
                    ))}

                  {!isEditing &&
                    pendingTranslations.map((pt) => (
                      <PendingTranslationRow
                        key={pt._key}
                        pt={pt}
                        languages={languages}
                        onDelete={(key) =>
                          setPendingTranslations((prev) => prev.filter((p) => p._key !== key))
                        }
                        onEdit={(key, updated) =>
                          setPendingTranslations((prev) =>
                            prev.map((p) => (p._key === key ? { ...p, ...updated } : p))
                          )
                        }
                      />
                    ))}

                  <AddTranslationForm
                    languages={languages}
                    existingLanguageIds={existingTranslationLangIds}
                    setId={setId}
                    defaultLanguageId={defaultTranslationLanguageId}
                    itemId={isEditing ? item.id : undefined}
                    onAdd={
                      !isEditing
                        ? (pt) =>
                            setPendingTranslations((prev) => [
                              ...prev,
                              { ...pt, _key: crypto.randomUUID() },
                            ])
                        : undefined
                    }
                  />
                </div>

                <div className="flex flex-col gap-2.5 min-w-0">
                  <SectionHeading>Synonyms</SectionHeading>
                  {isEditing ? (
                    <SynonymsSection
                      itemId={item.id}
                      languageId={item.language_id}
                    />
                  ) : (
                    <SynonymsSection
                      languageId={langId ? Number(langId) : null}
                      pendingTerms={pendingSynonyms}
                      onChangePending={setPendingSynonyms}
                    />
                  )}
                </div>
              </div>
            </div>
          </form>
        </div>

        {/* Footer */}
        <DialogFooter className="shrink-0 !mx-0 !mb-0">
          <Button type="submit" form="item-edit-form" disabled={isPending}>
            {isPending
              ? isEditing
                ? 'Saving…'
                : 'Adding…'
              : isEditing
                ? 'Save Changes'
                : 'Add Item'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
