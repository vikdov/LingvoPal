import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { PlusIcon, GitForkIcon, Volume2Icon, FlagIcon } from 'lucide-react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { useAllLanguages } from '@/features/languages';
import { useItemDetail, useItemSynonyms } from '../hooks/useSetsQuery';
import { difficultyLabel, langName } from '../utils/formatters';
import { ReportDialog } from './ReportDialog';
import type { ItemSummaryResponse } from '../types/sets.types';

interface ItemDetailSheetProps {
  item: ItemSummaryResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddToSet: () => void;
  onFork: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Draft',
  COMMUNITY: 'Community',
  APPROVED: 'Approved',
  OFFICIAL: 'Official',
};

const STATUS_VARIANTS: Record<string, 'outline' | 'secondary' | 'default'> = {
  DRAFT: 'outline',
  COMMUNITY: 'secondary',
  APPROVED: 'default',
  OFFICIAL: 'default',
};

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-1.5">
      {children}
    </p>
  );
}

export function ItemDetailSheet({ item, open, onOpenChange, onAddToSet, onFork }: ItemDetailSheetProps) {
  const { user } = useAuth();
  const { data: languages = [] } = useAllLanguages();
  const { data: detail, isLoading } = useItemDetail(open && item ? item.id : null);
  const { data: synonyms = [] } = useItemSynonyms(open && item ? item.id : undefined);
  const [reportOpen, setReportOpen] = useState(false);
  const [playingAudio, setPlayingAudio] = useState<'word' | 'context' | null>(null);

  function playAudio(url: string, type: 'word' | 'context') {
    setPlayingAudio(type);
    const audio = new Audio(url);
    audio.play().catch(() => {});
    audio.onended = () => setPlayingAudio(null);
  }

  const canReport = detail && detail.status !== 'draft' && detail.creator_id !== user?.id;
  const hasImage = !!detail?.image_url;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-3xl max-h-[85vh] flex flex-col p-0 gap-0 overflow-hidden">
          {/* Loading state */}
          {isLoading || !detail ? (
            <>
              <DialogHeader className="px-8 pt-7 pb-5 border-b">
                <DialogTitle className="text-xl">{item?.term ?? '…'}</DialogTitle>
              </DialogHeader>
              <div className="flex-1 overflow-y-auto px-8 py-6 flex flex-col gap-5">
                <Skeleton className="h-52 w-full rounded-lg" />
                <div className="flex gap-2">
                  <Skeleton className="h-5 w-20 rounded-full" />
                  <Skeleton className="h-5 w-16 rounded-full" />
                  <Skeleton className="h-5 w-14 rounded-full" />
                </div>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            </>
          ) : (
            <>
              {/* Hero image — full width, above header */}
              {hasImage && (
                <div className="w-full h-52 overflow-hidden shrink-0 bg-muted">
                  <img
                    src={detail.image_url!}
                    alt={detail.term}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* Header */}
              <DialogHeader className="px-8 pt-6 pb-4 border-b shrink-0">
                <div className="flex items-center gap-3 pr-8">
                  <DialogTitle className="text-2xl font-bold tracking-tight">
                    {detail.term}
                  </DialogTitle>
                  {detail.audio_url && (
                    <button
                      type="button"
                      onClick={() => playAudio(detail.audio_url!, 'word')}
                      className="text-muted-foreground hover:text-primary transition-colors shrink-0"
                      title="Play pronunciation"
                    >
                      <Volume2Icon className={`size-5 ${playingAudio === 'word' ? 'text-primary' : ''}`} />
                    </button>
                  )}
                </div>
                {/* Badges row */}
                <div className="flex flex-wrap gap-1.5 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {langName(detail.language_id, languages)}
                  </Badge>
                  {detail.part_of_speech && (
                    <Badge variant="outline" className="text-xs capitalize">
                      {detail.part_of_speech}
                    </Badge>
                  )}
                  {detail.difficulty != null && (
                    <Badge variant="secondary" className="text-xs">
                      {difficultyLabel(detail.difficulty)}
                    </Badge>
                  )}
                  <Badge variant={STATUS_VARIANTS[detail.status] ?? 'outline'} className="text-xs">
                    {STATUS_LABELS[detail.status] ?? detail.status}
                  </Badge>
                </div>
              </DialogHeader>

              {/* Scrollable body */}
              <div className="flex-1 overflow-y-auto px-8 py-6 flex flex-col gap-6">

                {/* Context */}
                {detail.context && (
                  <div>
                    <SectionLabel>Context sentence</SectionLabel>
                    <div className="flex items-start gap-3 rounded-lg bg-muted/50 px-4 py-3">
                      <p className="flex-1 text-base italic text-foreground leading-relaxed">
                        &ldquo;{detail.context}&rdquo;
                      </p>
                      {detail.context_audio_url && (
                        <button
                          type="button"
                          onClick={() => playAudio(detail.context_audio_url!, 'context')}
                          className="text-muted-foreground hover:text-primary transition-colors mt-0.5 shrink-0"
                          title="Play context audio"
                        >
                          <Volume2Icon className={`size-4 ${playingAudio === 'context' ? 'text-primary' : ''}`} />
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Lemma + Synonyms side by side when both exist */}
                {(detail.lemma || synonyms.length > 0) && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    {detail.lemma && (
                      <div>
                        <SectionLabel>Dictionary form</SectionLabel>
                        <p className="text-base font-medium">{detail.lemma}</p>
                      </div>
                    )}
                    {synonyms.length > 0 && (
                      <div>
                        <SectionLabel>Synonyms / variants</SectionLabel>
                        <div className="flex flex-wrap gap-1.5">
                          {synonyms.map((s) => (
                            <Badge key={s} variant="secondary" className="text-xs font-normal">
                              {s}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Translations */}
                {detail.translations.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <SectionLabel>Translations</SectionLabel>
                      <div className="flex flex-col gap-3">
                        {detail.translations.map((t) => (
                          <div key={t.id} className="flex flex-col gap-0.5 rounded-lg border border-border px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="text-base font-semibold">{t.term_trans}</span>
                              <Badge variant="outline" className="text-[10px] py-0 h-4 font-normal">
                                {langName(t.language_id, languages)}
                              </Badge>
                            </div>
                            {t.context_trans && (
                              <p className="text-sm text-muted-foreground italic mt-0.5">
                                &ldquo;{t.context_trans}&rdquo;
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Footer */}
              <div className="shrink-0 border-t px-8 py-4 flex items-center gap-3 bg-background">
                {canReport && (
                  <button
                    type="button"
                    onClick={() => setReportOpen(true)}
                    className="text-muted-foreground/50 hover:text-destructive transition-colors p-1 mr-auto"
                    title="Report this expression"
                  >
                    <FlagIcon className="size-4" />
                  </button>
                )}
                <Button onClick={onAddToSet} className={canReport ? '' : 'ml-auto'}>
                  <PlusIcon className="size-4" />
                  Add to Set
                </Button>
                <Button variant="outline" onClick={onFork}>
                  <GitForkIcon className="size-4" />
                  Fork
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {canReport && detail && (
        <ReportDialog
          targetId={detail.id}
          targetType="item"
          open={reportOpen}
          onOpenChange={setReportOpen}
        />
      )}
    </>
  );
}
