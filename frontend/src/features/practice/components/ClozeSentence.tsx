import { useRef, useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import type { AnswerLifecycle } from '../types/practice.types';

interface ClozeSentenceProps {
  clozePrefix: string | null;
  clozeWord: string | null;
  clozeSuffix: string | null;
  context: string | null;
  answer: string;
  lifecycle: AnswerLifecycle;
  userAnswer: string;
  posColorClass: string;
  inputValue: string;
  onInputChange: (v: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

const INPUT_FONT_CLASSES = 'text-3xl font-medium';

// All 4 borders always allocated (transparent when unfocused) — no layout shift on focus
const BASE_INPUT_CLASSES =
  'inline border-2 border-t-transparent border-l-transparent border-r-transparent border-b-foreground bg-transparent ' +
  'text-center outline-none focus:border-primary transition-colors';

function ColorCodedAnswer({ answer, userAnswer }: { answer: string; userAnswer: string }) {
  return (
    <>
      {answer.split('').map((char, i) => {
        const userChar = userAnswer[i];
        const colorClass =
          userChar === undefined
            ? 'text-muted-foreground'
            : userChar.toLowerCase() === char.toLowerCase()
              ? 'text-emerald-600'
              : 'text-red-500';
        return (
          <span key={i} className={colorClass}>
            {char}
          </span>
        );
      })}
    </>
  );
}

export function ClozeSentence({
  clozePrefix,
  clozeWord,
  clozeSuffix,
  context,
  answer,
  lifecycle,
  userAnswer,
  posColorClass,
  inputValue,
  onInputChange,
  onSubmit,
  isSubmitting,
}: ClozeSentenceProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const rulerRef = useRef<HTMLSpanElement>(null);
  const [inputWidth, setInputWidth] = useState(0);

  useEffect(() => {
    if (rulerRef.current) setInputWidth(rulerRef.current.offsetWidth);
  }, [answer]);

  useEffect(() => {
    if ((lifecycle === 'unanswered' || lifecycle === 'retrying') && !isSubmitting) {
      inputRef.current?.focus();
    }
  }, [lifecycle, isSubmitting]);

  const capitalize = clozePrefix === '';
  const displayAnswer = capitalize ? answer.charAt(0).toUpperCase() + answer.slice(1) : answer;

  const widthPx = `${Math.max(inputWidth + 12, 28)}px`;

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      if (!isSubmitting && inputValue.trim()) onSubmit();
    }
  }

  // Normal input slot (unanswered state)
  const clozeInput = (
    <span className="inline-flex items-end mx-1">
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isSubmitting}
        maxLength={answer.length}
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        style={{ width: widthPx }}
        className={cn(BASE_INPUT_CLASSES, INPUT_FONT_CLASSES, isSubmitting && 'opacity-50 cursor-not-allowed')}
      />
    </span>
  );

  // Retry slot: colored answer overlaid inside the input.
  // inputValue === '' → colored answer visible, input text transparent (caret still shows).
  // User types → colored answer hidden, input text visible.
  const retrySlot = (
    <span className="relative inline-flex items-end mx-1">
      {inputValue === '' && (
        <span
          aria-hidden
          className={cn(
            'absolute inset-0 flex items-center justify-center pointer-events-none select-none',
            INPUT_FONT_CLASSES,
          )}
        >
          <ColorCodedAnswer answer={displayAnswer} userAnswer={userAnswer} />
        </span>
      )}
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isSubmitting}
        maxLength={answer.length}
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        style={{ width: widthPx }}
        className={cn(
          BASE_INPUT_CLASSES,
          INPUT_FONT_CLASSES,
          // Hide typed text while showing colored overlay; caret remains visible
          inputValue === '' && 'text-transparent caret-foreground',
          isSubmitting && 'opacity-50 cursor-not-allowed',
        )}
      />
    </span>
  );

  let content: React.ReactNode;

  if (lifecycle === 'unanswered') {
    if (clozePrefix !== null && clozeWord !== null && clozeSuffix !== null) {
      content = (
        <p className="text-3xl text-center leading-relaxed">
          {clozePrefix}{clozeInput}{clozeSuffix}
        </p>
      );
    } else {
      content = (
        <div className="flex flex-col items-center gap-3">
          {context && <p className="text-3xl text-center leading-relaxed">{context}</p>}
          <div className="flex items-center gap-2">{clozeInput}</div>
        </div>
      );
    }
  } else if (lifecycle === 'correct' || lifecycle === 'corrected') {
    const baseWord = clozeWord ?? answer;
    const displayWord = capitalize ? baseWord.charAt(0).toUpperCase() + baseWord.slice(1) : baseWord;
    if (clozePrefix !== null && clozeSuffix !== null) {
      content = (
        <p className="text-3xl text-center leading-relaxed">
          {clozePrefix}
          <span className={cn('mx-1 font-semibold underline underline-offset-4', posColorClass)}>
            {displayWord}
          </span>
          {clozeSuffix}
        </p>
      );
    } else {
      content = (
        <div className="flex flex-col items-center gap-2">
          {context && <p className="text-3xl text-center leading-relaxed">{context}</p>}
          <span className={cn('text-3xl font-semibold', posColorClass)}>{displayWord}</span>
        </div>
      );
    }
  } else {
    // retrying — same inline slot, colored answer overlaid in the input field
    if (clozePrefix !== null && clozeWord !== null && clozeSuffix !== null) {
      content = (
        <p className="text-3xl text-center leading-relaxed">
          {clozePrefix}{retrySlot}{clozeSuffix}
        </p>
      );
    } else {
      content = (
        <div className="flex flex-col items-center gap-3">
          {context && <p className="text-3xl text-center leading-relaxed">{context}</p>}
          <div className="flex items-center gap-2">{retrySlot}</div>
        </div>
      );
    }
  }

  return (
    <>
      <span
        ref={rulerRef}
        aria-hidden
        className={cn('fixed top-0 left-0 invisible pointer-events-none whitespace-pre', INPUT_FONT_CLASSES)}
      >
        {displayAnswer}
      </span>
      {content}
    </>
  );
}
