import { useState, useEffect, useRef, useCallback } from 'react';
import { FlagIcon } from 'lucide-react';
import { useBrowserZoomScale } from '../hooks/useBrowserZoomScale';
import { usePracticeStore } from '../store/practice.store';
import { usePracticeSession } from '../hooks/usePracticeSession';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { getPosColor } from '../utils/posColors';
import { estimateNextReview } from '../utils/estimateNextReview';
import { ClozeSentence } from './ClozeSentence';
import { HintPanel } from './HintPanel';
import { MediaPanel } from './MediaPanel';
import { ReviewMeta } from './ReviewMeta';
import { NavigationControls } from './NavigationControls';
import { ConfidenceOverrideMenu } from './ConfidenceOverrideMenu';
import { ReportDialog } from '@/features/sets/components/ReportDialog';

export function PracticeCard() {
  const store = usePracticeStore();
  const { currentItem, currentAnswer, isLastItem, total, currentIndex } = usePracticeSession();
  const { user } = useAuth();

  const [inputValue, setInputValue] = useState('');
  const [estimatedNext, setEstimatedNext] = useState<Date | null>(null);
  const [hasAutoplayed, setHasAutoplayed] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    setInputValue('');
    setEstimatedNext(null);
    setHasAutoplayed(false);
    setIsSubmitting(false);
  }, [currentIndex]);

  const playAudio = useCallback((url: string) => {
    if (!url) return;
    try {
      if (audioRef.current) audioRef.current.pause();
      audioRef.current = new Audio(url);
      audioRef.current.play().catch(() => { });
    } catch {
      // ignore autoplay policy errors
    }
  }, []);

  useEffect(() => {
    if (!currentItem || !store.config.auto_play_audio) return;
    const lifecycle = currentAnswer?.lifecycle;
    if (lifecycle === 'correct') {
      const url = currentItem.context_audio_url ?? currentItem.audio_url;
      if (url) playAudio(url);
    } else if (lifecycle === 'retrying' && currentItem.audio_url && !hasAutoplayed) {
      playAudio(currentItem.audio_url);
      setHasAutoplayed(true);
    }
  }, [currentAnswer?.lifecycle, currentItem, store.config.auto_play_audio, hasAutoplayed, playAudio]);

  useEffect(() => {
    if (currentAnswer && currentItem && !estimatedNext) {
      setEstimatedNext(
        estimateNextReview(currentItem.last_reviewed, currentAnswer.isCorrect),
      );
    }
  }, [currentAnswer, currentItem, estimatedNext]);

  const zoomScale = useBrowserZoomScale();

  if (!currentItem) return null;

  const lifecycle = currentAnswer?.lifecycle ?? 'unanswered';
  const posColor = getPosColor(currentItem.part_of_speech);
  const answered = lifecycle !== 'unanswered';
  const navigationVisible = lifecycle === 'correct' || lifecycle === 'corrected';
  const canReport = currentItem.item_status !== 'draft' && currentItem.creator_id !== user?.id;

  function handleSubmit() {
    if (isSubmitting) return;
    if (lifecycle === 'unanswered') {
      setIsSubmitting(true);
      store.submitAnswer(inputValue);
      setIsSubmitting(false);
      setInputValue('');
    } else if (lifecycle === 'retrying') {
      if (inputValue.trim().toLowerCase() === currentItem.answer.toLowerCase()) {
        store.resolveRetype(currentItem.item_id);
        setInputValue('');
      } else {
        setInputValue('');
      }
    }
  }

  function handleNext() {
    if (isLastItem) store.finalise();
    else store.nextItem();
  }

  function handleArrow() {
    if (lifecycle === 'unanswered') {
      store.submitAnswer('');
    } else if (lifecycle === 'retrying') {
      store.resolveRetype(currentItem.item_id);
    } else {
      handleNext();
    }
  }

  return (
    // Three fixed zones: top (progress), middle (card), bottom (meta + nav)
    // No reflow between zones — hint slot always reserves space
    <div className="flex-1 flex flex-col bg-muted relative">

      {/* ── Top: progress ─────────────────────────────────────────────── */}
      <div className="flex flex-col h-14 shrink-0">
        <div className="h-1 bg-muted-foreground/20">
          <div
            className="h-full bg-navy transition-all duration-300 ease-out"
            style={{ width: `${((currentIndex + 1) / total) * 100}%` }}
          />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-navy font-semibold tabular-nums tracking-widest">
            {currentIndex + 1} / {total}
          </p>
        </div>
      </div>

      {/* ── Middle: main card content ──────────────────────────────────── */}
      <div className="flex flex-col items-center justify-center gap-8 px-8 pb-16 overflow-hidden" style={{ marginTop: `${60 * zoomScale}px` }}>

        {/* Image + POS label */}
        <MediaPanel
          imageUrl={store.config.show_images ? currentItem.image_url : null}
          showSoundIcon={answered && !!(currentItem.audio_url || currentItem.context_audio_url)}
          onSoundClick={() => {
            const url = lifecycle === 'correct' || lifecycle === 'corrected'
              ? (currentItem.context_audio_url ?? currentItem.audio_url)
              : currentItem.audio_url;
            if (url) playAudio(url);
          }}
          partOfSpeech={store.config.show_part_of_speech ? currentItem.part_of_speech : null}
          posColorClass={posColor.text}
          posHexColor={posColor.hex}
        />

        {/* Cloze sentence */}
        <div className="w-full max-w-xl">
          <ClozeSentence
            clozePrefix={currentItem.cloze_prefix}
            clozeWord={currentItem.cloze_word}
            clozeSuffix={currentItem.cloze_suffix}
            context={currentItem.context}
            answer={currentItem.answer}
            lifecycle={lifecycle}
            userAnswer={currentAnswer?.userAnswer ?? ''}
            posColorClass={posColor.text}
            posBorderClass={posColor.border}
            posHexColor={posColor.hex}
            inputValue={inputValue}
            onInputChange={setInputValue}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        </div>

        {/* Hint slot — fixed min-height so it never shifts the sentence up/down */}
        <div className="min-h-[3.5rem] flex flex-col items-center justify-center gap-1">
          {lifecycle === 'unanswered' && (
            <span className="text-xs text-muted-foreground/50 select-none">↵ Enter to submit</span>
          )}
          <HintPanel
            item={currentItem}
            config={store.config}
            lifecycle={lifecycle}
            posColorClass={posColor.text}
          />
        </div>
      </div>

      {/* ── Bottom: review meta + confidence + navigation ─────────────── */}
      <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-6 pb-5">
        <div className="flex items-end gap-2">
          <ReviewMeta
            lastReviewed={currentItem.last_reviewed}
            estimatedNext={estimatedNext}
            answered={answered}
          />
          {canReport && (
            <button
              type="button"
              onClick={() => setReportOpen(true)}
              className="text-muted-foreground/50 hover:text-destructive transition-colors p-1"
              title="Report this expression"
            >
              <FlagIcon className="size-3.5" />
            </button>
          )}
        </div>
        <div className="flex items-end gap-3">
          {navigationVisible && (
            <ConfidenceOverrideMenu
              itemId={currentItem.item_id}
              current={currentAnswer?.confidenceOverride ?? null}
              onSelect={store.setConfidenceOverride}
            />
          )}
          <NavigationControls
            visible={true}
            onNext={handleArrow}
          />
        </div>
      </div>

      {canReport && (
        <ReportDialog
          targetId={currentItem.item_id}
          targetType="item"
          open={reportOpen}
          onOpenChange={setReportOpen}
        />
      )}
    </div>
  );
}
