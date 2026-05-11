import { useRef, useState } from 'react';
import { toast } from 'sonner';
import { UploadCloudIcon, FileIcon, Loader2Icon, ImageIcon, AudioLinesIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { useAllLanguages } from '@/features/languages';
import { useAnkiConfirm, useAnkiPreview } from '../hooks/useAnkiImport';
import type { AnkiPreviewResponse, DetectedFieldInfo, FieldMapping } from '../types/import.types';

type Step = 'idle' | 'analyzing' | 'summary' | 'importing';

const NONE = '(none)';

function formatBytes(bytes: number): string {
  if (bytes === 0) return 'None';
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AnkiImportModal({ open, onOpenChange }: Props) {
  const [step, setStep] = useState<Step>('idle');
  const [preview, setPreview] = useState<AnkiPreviewResponse | null>(null);
  const [title, setTitle] = useState('');
  const [mapping, setMapping] = useState<FieldMapping>({ term_field: '' });
  const [sourceLangId, setSourceLangId] = useState<number | null>(null);
  const [targetLangId, setTargetLangId] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: languages = [] } = useAllLanguages();
  const previewMutation = useAnkiPreview();
  const confirmMutation = useAnkiConfirm();

  function reset() {
    setStep('idle');
    setPreview(null);
    setTitle('');
    setMapping({ term_field: '' });
    setSourceLangId(null);
    setTargetLangId(null);
    if (inputRef.current) inputRef.current.value = '';
  }

  function handleOpenChange(val: boolean) {
    if (!val) reset();
    onOpenChange(val);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    setStep('analyzing');
    previewMutation.mutate(file, {
      onSuccess: (data) => {
        setPreview(data);
        const title = data.deck_name && data.deck_name !== 'Default'
          ? data.deck_name
          : file.name.replace(/\.apkg$/i, '').replace(/[_-]+/g, ' ').trim();
        setTitle(title);
        setMapping(data.suggested_mapping);
        setStep('summary');
      },
      onError: (err) => {
        toast.error(err.message);
        setStep('idle');
      },
    });
  }

  function handleConfirm() {
    if (!preview || sourceLangId == null) return;

    setStep('importing');
    confirmMutation.mutate(
      {
        import_token: preview.import_token,
        source_lang_id: sourceLangId!,
        target_lang_id: targetLangId!,
        title: title.trim() || undefined,
        field_mapping: mapping,
      },
      {
        onSuccess: (data) => {
          const parts = [`${data.item_count} cards`];
          if (data.reused_count > 0) parts.push(`${data.reused_count} reused`);
          if (data.skipped_count > 0) parts.push(`${data.skipped_count} skipped`);
          if (data.no_gap_count > 0) parts.push(`${data.no_gap_count} skipped (no gap)`);
          toast.success(`Imported "${data.title}" — ${parts.join(', ')}.`);
          handleOpenChange(false);
        },
        onError: (err) => {
          toast.error(err.message);
          setStep('summary');
        },
      },
    );
  }

  const canConfirm = sourceLangId != null && mapping.term_field;

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Import from Anki</SheetTitle>
        </SheetHeader>

        <div className="flex flex-col gap-6 p-4">
          {step === 'idle' && <DropZone inputRef={inputRef} onFileChange={handleFileChange} />}
          {step === 'analyzing' && <CenteredMessage icon={<Loader2Icon className="size-8 animate-spin text-muted-foreground" />} text="Analyzing deck…" />}
          {step === 'importing' && <CenteredMessage icon={<Loader2Icon className="size-8 animate-spin text-primary" />} text="Creating set and importing cards…" />}
          {step === 'summary' && preview && (
            <SummaryForm
              preview={preview}
              title={title}
              mapping={mapping}
              sourceLangId={sourceLangId}
              targetLangId={targetLangId}
              languages={languages}
              onTitleChange={setTitle}
              onMappingChange={setMapping}
              onSourceLangChange={setSourceLangId}
              onTargetLangChange={setTargetLangId}
            />
          )}
        </div>

        <SheetFooter className="px-4 pb-4">
          {step === 'summary' ? (
            <div className="flex w-full gap-2">
              <Button variant="outline" className="flex-1" onClick={() => handleOpenChange(false)}>
                Cancel
              </Button>
              <Button className="flex-1" disabled={!canConfirm} onClick={handleConfirm}>
                Confirm Import
              </Button>
            </div>
          ) : (
            <Button variant="outline" className="w-full" onClick={() => handleOpenChange(false)}>
              Cancel
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function DropZone({
  inputRef,
  onFileChange,
}: {
  inputRef: React.RefObject<HTMLInputElement | null>;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Upload an Anki package file (.apkg) to import its cards as a new vocabulary set.
        Images and audio are imported automatically.
      </p>
      <input ref={inputRef} type="file" accept=".apkg" className="sr-only" onChange={onFileChange} />
      <button
        type="button"
        className="flex flex-col items-center gap-3 rounded-lg border-2 border-dashed border-border p-10 text-center transition-colors hover:border-primary hover:bg-muted/50"
        onClick={() => inputRef.current?.click()}
      >
        <UploadCloudIcon className="size-10 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium">Drop your .apkg file here</p>
          <p className="text-xs text-muted-foreground">or click to browse</p>
        </div>
      </button>
    </div>
  );
}

function CenteredMessage({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex flex-col items-center gap-4 py-12">
      {icon}
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );
}

interface SummaryFormProps {
  preview: AnkiPreviewResponse;
  title: string;
  mapping: FieldMapping;
  sourceLangId: number | null;
  targetLangId: number | null;
  languages: { id: number; name: string }[];
  onTitleChange: (v: string) => void;
  onMappingChange: (m: FieldMapping) => void;
  onSourceLangChange: (id: number) => void;
  onTargetLangChange: (id: number | null) => void;
}

function SummaryForm({
  preview,
  title,
  mapping,
  sourceLangId,
  targetLangId,
  languages,
  onTitleChange,
  onMappingChange,
  onSourceLangChange,
  onTargetLangChange,
}: SummaryFormProps) {
  const fields = preview.detected_fields;

  function set(key: keyof FieldMapping, value: string | null | undefined) {
    onMappingChange({ ...mapping, [key]: value === NONE ? null : value });
  }

  function val(key: keyof FieldMapping): string {
    const v = mapping[key];
    return v ?? NONE;
  }

  const hasMedia = fields.some((f) => f.has_image || f.has_audio);

  return (
    <div className="flex flex-col gap-5">
      {/* Stats */}
      <div className="rounded-lg bg-muted/50 p-4 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-sm">
          <FileIcon className="size-4 shrink-0 text-muted-foreground" />
          <span className="font-medium truncate">{title}</span>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground pl-6">
          <span>{preview.card_count.toLocaleString()} cards</span>
          <span>{preview.detected_fields.length} fields detected</span>
          {preview.media_size_bytes > 0 && (
            <span className="flex items-center gap-1">
              <ImageIcon className="size-3" />
              {formatBytes(preview.media_size_bytes)} media
            </span>
          )}
        </div>
      </div>

      <Separator />

      {/* Set title */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="import-title">Set Title</Label>
        <Input
          id="import-title"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="Deck name"
        />
      </div>

      <Separator />

      {/* Field mapping */}
      <div className="flex flex-col gap-3">
        <div>
          <p className="text-sm font-medium">Field Mapping</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Map Anki fields to LingvoPal item fields. Optional fields can be left empty.
          </p>
        </div>

        <FieldSelect
          id="map-term"
          label="Term"
          required
          value={val('term_field')}
          fields={fields}
          includeNone={false}
          onChange={(v) => set('term_field', v)}
        />
        <FieldSelect
          id="map-translation"
          label="Translation"
          value={val('translation_field')}
          fields={fields}
          onChange={(v) => set('translation_field', v)}
        />
        <FieldSelect
          id="map-context"
          label="Context Sentence"
          value={val('context_field')}
          fields={fields}
          onChange={(v) => set('context_field', v)}
        />
        <FieldSelect
          id="map-context-trans"
          label="Context Sentence (translated)"
          value={val('context_trans_field')}
          fields={fields}
          onChange={(v) => set('context_trans_field', v)}
        />
        <FieldSelect
          id="map-lemma"
          label="Transcription / Base Form"
          value={val('lemma_field')}
          fields={fields}
          onChange={(v) => set('lemma_field', v)}
        />
        <FieldSelect
          id="map-pos"
          label="Part of Speech"
          value={val('part_of_speech_field')}
          fields={fields}
          onChange={(v) => set('part_of_speech_field', v)}
        />

        {/* Image field — only show fields that contain image syntax */}
        <FieldSelectWithBadge
          id="map-image"
          label="Image"
          badge={<Badge variant="secondary" className="text-[10px] gap-0.5 py-0"><ImageIcon className="size-2.5" />media</Badge>}
          hint="Field must contain <img src=...> — will upload to storage"
          value={val('image_field')}
          fields={fields.filter((f) => f.has_image || val('image_field') === f.name)}
          allFields={fields}
          onChange={(v) => set('image_field', v)}
        />

        {/* Audio field — only show fields that contain sound syntax */}
        <FieldSelectWithBadge
          id="map-audio"
          label="Expression Audio"
          badge={<Badge variant="secondary" className="text-[10px] gap-0.5 py-0"><AudioLinesIcon className="size-2.5" />media</Badge>}
          hint="Field must contain [sound:...] — will upload to storage"
          value={val('audio_field')}
          fields={fields.filter((f) => f.has_audio || val('audio_field') === f.name)}
          allFields={fields}
          onChange={(v) => set('audio_field', v)}
        />

        {!hasMedia && (
          <p className="text-xs text-muted-foreground">
            No media fields detected in this deck.
          </p>
        )}
      </div>

      <Separator />

      {/* Language pair */}
      <div className="flex flex-col gap-3">
        <div>
          <p className="text-sm font-medium">Language Pair</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Used to categorize the set. Source and target can be the same language.
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          {/* Added red asterisk to match 'Term *' styling */}
          <Label htmlFor="source-lang" className="text-xs text-muted-foreground flex items-center gap-1">
            Terms are written in…
            <span className="text-destructive">*</span>
          </Label>
          <Select
            value={sourceLangId != null ? String(sourceLangId) : ''}
            onValueChange={(v) => onSourceLangChange(Number(v))}
          >
            <SelectTrigger id="source-lang">
              <SelectValue placeholder="Select language…" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((l) => (
                <SelectItem key={l.id} value={String(l.id)}>{l.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="target-lang" className="text-xs text-muted-foreground">
            Translations are written in…
          </Label>
          <Select
            // Use empty string when null to ensure placeholder "Select language..." shows
            value={targetLangId != null ? String(targetLangId) : ""}
            onValueChange={(v) => onTargetLangChange(v === NONE ? null : Number(v))}
          >
            <SelectTrigger id="target-lang">
              <SelectValue placeholder="Select language…" />
            </SelectTrigger>
            <SelectContent>
              {/* Added NONE constant to match field styling in image_641fc2.png */}
              <SelectItem value={NONE}>{NONE}</SelectItem>
              {languages.map((l) => (
                <SelectItem key={l.id} value={String(l.id)}>{l.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}

// ── Field selects ─────────────────────────────────────────────────────────────

interface FieldSelectProps {
  id: string;
  label: string;
  required?: boolean;
  value: string;
  fields: DetectedFieldInfo[];
  includeNone?: boolean;
  onChange: (v: string) => void;
}

function FieldSelect({
  id,
  label,
  required,
  value,
  fields,
  includeNone = true,
  onChange,
}: FieldSelectProps) {
  const current = fields.find((f) => f.name === value);
  const sample = current?.sample;

  return (
    <div className="flex flex-col gap-1">
      <Label htmlFor={id} className="text-xs text-muted-foreground flex items-center gap-1">
        {label}
        {required && <span className="text-destructive">*</span>}
      </Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id={id}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {includeNone && <SelectItem value={NONE}>(none)</SelectItem>}
          {fields.map((f) => (
            <SelectItem key={f.name} value={f.name}>
              <span className="flex items-center gap-1.5">
                {f.name}
                {f.has_image && <ImageIcon className="size-3 text-muted-foreground" />}
                {f.has_audio && <AudioLinesIcon className="size-3 text-muted-foreground" />}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {sample && value !== NONE && (
        <p className="text-[11px] text-muted-foreground truncate pl-1">e.g. "{sample}"</p>
      )}
    </div>
  );
}

interface FieldSelectWithBadgeProps extends Omit<FieldSelectProps, 'fields'> {
  badge: React.ReactNode;
  hint: string;
  fields: DetectedFieldInfo[];   // pre-filtered fields shown first
  allFields: DetectedFieldInfo[]; // full list as fallback
}

function FieldSelectWithBadge({
  id,
  label,
  badge,
  hint,
  value,
  fields,
  allFields,
  onChange,
}: FieldSelectWithBadgeProps) {
  const displayFields = fields.length > 0 ? fields : allFields;

  return (
    <div className="flex flex-col gap-1">
      <Label htmlFor={id} className="text-xs text-muted-foreground flex items-center gap-1.5">
        {label} {badge}
      </Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id={id}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE}>(none)</SelectItem>
          {displayFields.map((f) => (
            <SelectItem key={f.name} value={f.name}>{f.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      {value !== NONE && (
        <p className="text-[11px] text-muted-foreground pl-1">{hint}</p>
      )}
    </div>
  );
}
