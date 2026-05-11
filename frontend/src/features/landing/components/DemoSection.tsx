import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { FadeUp } from '@/components/ui/animate';

const ANSWER = 'leggevo';
const BEFORE = 'Da bambino, ';
const AFTER = ' ogni sera fino a mezzanotte.';
const TRANSLATION = '"As a boy, I used to read every evening until midnight."';

type Phase = 'idle' | 'typing' | 'correct';

function useDemoLoop() {
  const [phase, setPhase] = useState<Phase>('idle');
  const [typed, setTyped] = useState('');

  useEffect(() => {
    let t: ReturnType<typeof setTimeout>;

    if (phase === 'idle') {
      t = setTimeout(() => setPhase('typing'), 1800);
    } else if (phase === 'typing') {
      if (typed.length < ANSWER.length) {
        t = setTimeout(
          () => setTyped(ANSWER.slice(0, typed.length + 1)),
          typed.length === 0 ? 400 : 210,
        );
      } else {
        t = setTimeout(() => setPhase('correct'), 380);
      }
    } else {
      t = setTimeout(() => {
        setTyped('');
        setPhase('idle');
      }, 2600);
    }

    return () => clearTimeout(t);
  }, [phase, typed]);

  return { phase, typed };
}

export function DemoSection() {
  const { phase, typed } = useDemoLoop();
  const isCorrect = phase === 'correct';
  const isIdle = phase === 'idle' && typed.length === 0;

  return (
    <section className="flex flex-col items-center gap-8 px-6 py-20 bg-card border-y border-border">
      <FadeUp>
        <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
          <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> Interaction preview
        </Badge>
      </FadeUp>

      <FadeUp delay={0.06}>
        <div className="flex flex-col items-center gap-2 text-center">
          <h2
            className="font-bold tracking-[-0.03em] text-foreground"
            style={{ fontSize: 'clamp(2rem, 3.5vw, 2.75rem)' }}
          >
            This is the entire learning loop.
          </h2>
          <p className="text-[0.9375rem] text-muted-foreground">
            This is exactly what you'll do every day.
          </p>
        </div>
      </FadeUp>

      <FadeUp delay={0.14}>
      <div
        className="w-full max-w-[680px] rounded-xl overflow-hidden border border-border"
        style={{ boxShadow: '0 32px 64px -32px rgba(0,0,0,0.5)' }}
      >
        <div className="flex items-center gap-1.5 px-4 py-3 bg-muted border-b border-border">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
          <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            lingvopal — practice
          </span>
        </div>

        <div className="px-8 py-6 bg-background flex flex-col gap-5">
          <div className="flex items-baseline justify-between gap-4 pb-4 border-b border-border">
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Specimen — Italian · verb · imperfetto
            </span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground shrink-0">
              leggere
            </span>
          </div>

          <p
            className="leading-relaxed text-foreground"
            style={{ fontSize: 'clamp(1.125rem, 2vw, 1.5rem)' }}
          >
            {BEFORE}
            <GapWord typed={typed} isCorrect={isCorrect} isIdle={isIdle} />
            {AFTER}
          </p>

          <p className="text-[0.9375rem] text-muted-foreground italic leading-relaxed">
            {TRANSLATION}
          </p>

          <div className="flex gap-1.5 flex-wrap pt-4 border-t border-border">
            <Chip>new word</Chip>
            <Chip>interval · 6h</Chip>
            {isCorrect
              ? <Chip accent>✓ correct · next review tomorrow</Chip>
              : <Chip>SM-2 · ease 2.5</Chip>}
          </div>
        </div>
      </div>
      </FadeUp>

      <FadeUp delay={0.2}>
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          Auto-demo — try it live after signing up
        </p>
      </FadeUp>
    </section>
  );
}

interface GapWordProps {
  typed: string;
  isCorrect: boolean;
  isIdle: boolean;
}

function GapWord({ typed, isCorrect, isIdle }: GapWordProps) {
  const isEmpty = isIdle && typed.length === 0;
  const isTyping = !isEmpty && !isCorrect;

  const color = isCorrect
    ? '#78AFA7'
    : isEmpty
      ? 'var(--muted-foreground)'
      : '#D96374';

  const bg = isCorrect
    ? 'rgba(120,175,167,0.1)'
    : isEmpty
      ? 'transparent'
      : 'rgba(217,99,116,0.08)';

  const borderColor = isCorrect
    ? '#78AFA7'
    : isEmpty
      ? 'var(--border)'
      : '#D96374';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'baseline',
        padding: '0.05em 0.3em',
        fontFamily: 'monospace',
        fontWeight: 500,
        fontSize: '0.92em',
        color,
        background: bg,
        borderBottom: `2px solid ${borderColor}`,
        transition: 'color 0.25s, background 0.25s, border-color 0.25s',
        minWidth: '5.5ch',
        verticalAlign: 'baseline',
        lineHeight: 1.4,
      }}
    >
      {isEmpty ? '___' : typed.length === 0 ? ' ' : typed}
      {isTyping && (
        <span
          aria-hidden
          style={{
            display: 'inline-block',
            width: '2px',
            height: '0.9em',
            marginLeft: '1px',
            background: 'var(--primary)',
            animation: 'lp-cursor-blink 1.05s steps(1) infinite',
            verticalAlign: 'middle',
            flexShrink: 0,
          }}
        />
      )}
    </span>
  );
}

function Chip({ children, accent }: { children: React.ReactNode; accent?: boolean }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        'font-mono text-[10px] tracking-widest uppercase rounded-sm transition-colors',
        accent
          ? 'border-[rgba(120,175,167,0.4)] text-[#78AFA7] bg-[rgba(120,175,167,0.06)]'
          : 'border-border text-muted-foreground',
      )}
    >
      {children}
    </Badge>
  );
}
