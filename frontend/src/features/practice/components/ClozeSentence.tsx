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
  posBorderClass: string;
  posHexColor: string;
  inputValue: string;
  onInputChange: (v: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

const INPUT_FONT_CLASSES = 'text-3xl font-semibold';

// pl-1 pr-2 = 4px left + 8px right → caret sits close to left but text has room
// py-1 + leading-none → box is font-size + 8px tall, caret is font-size tall → shorter caret
const BASE_INPUT_CLASSES =
  'inline border-[2px] bg-white pl-1 pr-2 py-1 leading-none outline-none transition-colors ' +
  '[&:not(:focus)]:border-t-transparent [&:not(:focus)]:border-l-transparent [&:not(:focus)]:border-r-transparent';

function ColorCodedAnswer({ answer, userAnswer }: { answer: string; userAnswer: string }) {
  return (
    <>
      {answer.split('').map((char, i) => {
        const userChar = userAnswer[i];
        const color =
          userChar === undefined
            ? 'text-[#f5a79b]'
            : userChar.toLowerCase() === char.toLowerCase()
              ? 'text-[#009687]'
              : 'text-[#f5a79b]';
        return (
          <span key={i} className={color}>
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
  posBorderClass,
  posHexColor,
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

  const widthPx = `${Math.max(inputWidth + 16, 24)}px`;

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      if (!isSubmitting) onSubmit();
    }
  }

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
        style={{ width: widthPx, caretColor: posHexColor, color: posHexColor }}
        className={cn(BASE_INPUT_CLASSES, INPUT_FONT_CLASSES, posBorderClass, isSubmitting && 'opacity-50 cursor-not-allowed')}
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
        style={{ width: widthPx, caretColor: posHexColor, color: posHexColor }}
        className={cn(
          BASE_INPUT_CLASSES,
          INPUT_FONT_CLASSES,
          posBorderClass,
          inputValue === '' && 'text-transparent',
          isSubmitting && 'opacity-50 cursor-not-allowed',
        )}
      />
    </span>
  );

  let content: React.ReactNode;

  if (lifecycle === 'unanswered') {
    if (clozePrefix !== null && clozeWord !== null && clozeSuffix !== null) {
      content = (
        <p className="text-3xl font-semibold text-center leading-relaxed text-navy">
          {clozePrefix}{clozeInput}{clozeSuffix}
        </p>
      );
    } else {
      content = (
        <div className="flex flex-col items-center gap-3">
          {context && <p className="text-3xl font-semibold text-center leading-relaxed text-navy">{context}</p>}
          <div className="flex items-center gap-2">{clozeInput}</div>
        </div>
      );
    }
  } else if (lifecycle === 'correct' || lifecycle === 'corrected') {
    const baseWord = clozeWord ?? answer;
    const displayWord = capitalize ? baseWord.charAt(0).toUpperCase() + baseWord.slice(1) : baseWord;
    if (clozePrefix !== null && clozeSuffix !== null) {
      content = (
        <p className="text-3xl font-semibold text-center leading-relaxed text-navy">
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
          {context && <p className="text-3xl font-semibold text-center leading-relaxed text-navy">{context}</p>}
          <span className={cn('text-3xl font-semibold', posColorClass)}>{displayWord}</span>
        </div>
      );
    }
  } else {
    if (clozePrefix !== null && clozeWord !== null && clozeSuffix !== null) {
      content = (
        <p className="text-3xl font-semibold text-center leading-relaxed text-navy">
          {clozePrefix}{retrySlot}{clozeSuffix}
        </p>
      );
    } else {
      content = (
        <div className="flex flex-col items-center gap-3">
          {context && <p className="text-3xl font-semibold text-center leading-relaxed text-navy">{context}</p>}
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
        className={cn('fixed top-0 left-0 invisible pointer-events-none whitespace-pre leading-none', INPUT_FONT_CLASSES)}
      >
        {displayAnswer}
      </span>
      {content}
    </>
  );
}
