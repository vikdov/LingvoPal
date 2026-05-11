import { useState, useEffect, useRef, useCallback } from 'react';
import { usePracticeStore } from '../store/practice.store';
import { usePracticeSession } from '../hooks/usePracticeSession';
import { getPosColor } from '../utils/posColors';
import { estimateNextReview } from '../utils/estimateNextReview';
import { ClozeSentence } from './ClozeSentence';
import { HintPanel } from './HintPanel';
import { MediaPanel } from './MediaPanel';
import { ReviewMeta } from './ReviewMeta';
import { NavigationControls } from './NavigationControls';
import { ConfidenceOverrideMenu } from './ConfidenceOverrideMenu';

export function PracticeCard() {
  const store = usePracticeStore();
  const { currentItem, currentAnswer, isLastItem, total, currentIndex } = usePracticeSession();

  const [inputValue, setInputValue] = useState('');
  const [estimatedNext, setEstimatedNext] = useState<Date | null>(null);
  const [hasAutoplayed, setHasAutoplayed] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
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
      audioRef.current.play().catch(() => {});
    } catch {
      // ignore autoplay policy errors
    }
  }, []);

  useEffect(() => {
    if (!currentItem || !store.config.auto_play_audio) return;
    const lifecycle = currentAnswer?.lifecycle;
    const audioUrl = currentItem.audio_url;
    if (lifecycle === 'correct' && audioUrl) {
      playAudio(audioUrl);
    } else if (lifecycle === 'retrying' && audioUrl && !hasAutoplayed) {
      playAudio(audioUrl);
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

  if (!currentItem) return null;

  const lifecycle = currentAnswer?.lifecycle ?? 'unanswered';
  const posColor = getPosColor(currentItem.part_of_speech);
  const answered = lifecycle !== 'unanswered';
  const navigationVisible = lifecycle === 'correct' || lifecycle === 'corrected';

  function handleSubmit() {
    if (isSubmitting || !inputValue.trim()) return;
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

  return (
    // Three fixed zones: top (progress), middle (card), bottom (meta + nav)
    // No reflow between zones — hint slot always reserves space
    <div className="flex-1 flex flex-col">

      {/* ── Top: progress ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-center h-14 shrink-0">
        <p className="text-sm text-muted-foreground font-medium tracking-wide">
          {currentIndex + 1} / {total}
        </p>
      </div>

      {/* ── Middle: main card content ──────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center gap-7 px-8 overflow-hidden">

        {/* Image + POS badge */}
        <div className="flex flex-col items-center gap-3">
          <MediaPanel
            imageUrl={store.config.show_images ? currentItem.image_url : null}
            showSoundIcon={answered && !!currentItem.audio_url}
            onSoundClick={() => currentItem.audio_url && playAudio(currentItem.audio_url)}
          />
          {store.config.show_part_of_speech && currentItem.part_of_speech && (
            <span className={`text-sm font-medium px-3 py-1 rounded-full ${posColor.bg} ${posColor.text}`}>
              {currentItem.part_of_speech}
            </span>
          )}
        </div>

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
            inputValue={inputValue}
            onInputChange={setInputValue}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        </div>

        {/* Hint slot — fixed min-height so it never shifts the sentence up/down */}
        <div className="min-h-[3.5rem] flex items-center">
          <HintPanel
            item={currentItem}
            config={store.config}
            lifecycle={lifecycle}
            posColorClass={posColor.text}
          />
        </div>
      </div>

      {/* ── Bottom: review meta + confidence + navigation ─────────────── */}
      <div className="flex items-end justify-between h-20 px-6 pb-6 shrink-0">
        <ReviewMeta
          lastReviewed={currentItem.last_reviewed}
          estimatedNext={estimatedNext}
          answered={answered}
        />
        <div className="flex items-end gap-3">
          {navigationVisible && (
            <ConfidenceOverrideMenu
              itemId={currentItem.item_id}
              current={currentAnswer?.confidenceOverride ?? null}
              onSelect={store.setConfidenceOverride}
            />
          )}
          <NavigationControls
            visible={navigationVisible}
            onNext={handleNext}
          />
        </div>
      </div>
    </div>
  );
}
