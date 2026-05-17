import { useState } from 'react';
import { toast } from 'sonner';
import { Volume2Icon, BookOpenIcon, LayersIcon } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAllLanguages } from '@/features/languages';
import { useCreatedSets, useAddExistingItemToSet } from '../hooks/useSetsQuery';
import { langName, difficultyLabel } from '../utils/formatters';
import type { ItemDetailResponse } from '../types/sets.types';

interface ItemViewModalProps {
  item: ItemDetailResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ItemViewModal({ item, open, onOpenChange }: ItemViewModalProps) {
  const [selectedSetId, setSelectedSetId] = useState<string>('');
  const { data: languages = [] } = useAllLanguages();
  const { data: createdSets } = useCreatedSets(0, 200);
  const addToSet = useAddExistingItemToSet();

  const sets = createdSets?.data ?? [];

  function handleAdd() {
    if (!selectedSetId) return;
    const setId = Number(selectedSetId);
    addToSet.mutate(
      { setId, itemId: item.id },
      {
        onSuccess: () => {
          toast.success(`"${item.term}" added to set.`);
          setSelectedSetId('');
          onOpenChange(false);
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }

  function handlePlayAudio(url: string) {
    try { new Audio(url).play().catch(() => {}); } catch { /* ignore */ }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-xl">{item.term}</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {item.image_url && (
            <img
              src={item.image_url}
              alt={item.term}
              className="w-full max-h-48 object-cover rounded-md"
            />
          )}

          {/* Meta badges */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="text-xs">
              <BookOpenIcon className="size-3" />
              {langName(item.language_id, languages)}
            </Badge>
            {item.part_of_speech && (
              <Badge variant="outline">{item.part_of_speech}</Badge>
            )}
            {item.difficulty !== null && (
              <Badge variant="secondary">{difficultyLabel(item.difficulty)}</Badge>
            )}
          </div>

          {/* Context sentence */}
          {item.context && (
            <p className="text-sm text-muted-foreground italic border-l-2 border-border pl-3">
              &ldquo;{item.context}&rdquo;
            </p>
          )}

          {/* Audio */}
          {(item.audio_url || item.context_audio_url) && (
            <div className="flex gap-2">
              {item.audio_url && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handlePlayAudio(item.audio_url!)}
                >
                  <Volume2Icon className="size-3.5" />
                  Word audio
                </Button>
              )}
              {item.context_audio_url && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handlePlayAudio(item.context_audio_url!)}
                >
                  <Volume2Icon className="size-3.5" />
                  Sentence audio
                </Button>
              )}
            </div>
          )}

          {/* Translations */}
          {item.translations.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Translations
              </p>
              <div className="flex flex-col gap-1">
                {item.translations.map((t) => (
                  <div key={t.id} className="rounded-md bg-muted/50 px-3 py-2">
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

          {/* Add to set */}
          {sets.length > 0 && (
            <div className="flex flex-col gap-2 pt-2 border-t border-border">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Add to my set
              </p>
              <div className="flex gap-2">
                <Select value={selectedSetId} onValueChange={setSelectedSetId}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Choose a set…">
                      {selectedSetId ? (
                        <span className="flex items-center gap-1.5">
                          <LayersIcon className="size-3.5" />
                          {sets.find((s) => String(s.id) === selectedSetId)?.title}
                        </span>
                      ) : (
                        'Choose a set…'
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {sets.map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>
                        {s.title}
                        <span className="ml-1.5 text-xs text-muted-foreground">
                          ({s.item_count})
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  disabled={!selectedSetId || addToSet.isPending}
                  onClick={handleAdd}
                >
                  {addToSet.isPending ? 'Adding…' : 'Add'}
                </Button>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
