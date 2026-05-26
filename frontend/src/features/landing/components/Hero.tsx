import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FadeIn } from '@/components/ui/animate';

const EASE = [0.22, 0.1, 0.36, 1] as const;

export function Hero() {
  return (
    <section className="relative flex flex-col items-center text-center px-6 pt-24 pb-20 overflow-hidden gap-5">
      {/* Dot grid */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(var(--border) 1px, transparent 1px),' +
            'linear-gradient(90deg, var(--border) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          maskImage:
            'radial-gradient(ellipse 80% 60% at 50% 0%, black 40%, transparent 100%)',
        }}
      />
      {/* Radial glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute"
        style={{
          top: '-80px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '600px',
          height: '300px',
          background:
            'radial-gradient(ellipse, rgba(99,102,241,0.22) 0%, rgba(139,92,246,0.1) 40%, transparent 70%)',
        }}
      />

      <FadeIn delay={0} duration={0.4}>
        <p className="relative font-mono text-[12px] font-medium tracking-widest uppercase text-muted-foreground">
          For learners who want to actually remember, not just recognize.
        </p>
      </FadeIn>

      <FadeIn delay={0.04} duration={0.4}>
        <Badge
          variant="outline"
          className="relative font-mono text-[12px] text-indigo-600 bg-indigo-500/5 border-indigo-700/30 gap-1.5 rounded-full"
        >
          <span aria-hidden>✦</span> Active recall · Spaced repetition
        </Badge>
      </FadeIn>

      <FadeIn delay={0.08} duration={0.4}>
        <h1
          className="relative font-bold tracking-[-0.04em] leading-none text-foreground"
          style={{ fontSize: 'clamp(2.5rem, 6vw, 4.5rem)' }}
        >
          Learn a language by{' '}
          <span className="bg-gradient-to-r from-sky-400 via-indigo-400 to-indigo-600 bg-clip-text text-transparent">
            writing
          </span>{' '}
          it.
        </h1>
      </FadeIn>

      <FadeIn delay={0.13} duration={0.4}>
        <p className="relative text-[1.0625rem] font-semibold text-foreground max-w-[34ch]">
          You don't recognize words — you produce them.
        </p>
      </FadeIn>

      <FadeIn delay={0.17} duration={0.4}>
        <p className="relative text-[0.9375rem] text-muted-foreground max-w-[40ch] leading-relaxed">
          No multiple choice. No guessing. Type the word from memory, in context — every time.
        </p>
      </FadeIn>

      <FadeIn delay={0.20} duration={0.4}>
        <p className="relative font-mono text-[12px] font-medium italic text-foreground/50">
          It's harder than tapping pictures. That's exactly why it works.
        </p>
      </FadeIn>

      <FadeIn delay={0.24} duration={0.4}>
        <div className="relative flex items-center gap-3 flex-wrap justify-center mt-1">
          <Button
            asChild
            className="shimmer-btn px-6 py-2.5 h-auto text-[14px]"
            style={{
              boxShadow:
                '0 0 24px -6px rgba(99,102,241,0.5), 0 1px 0 rgba(255,255,255,0.08) inset',
            }}
          >
            <Link to="/auth/register">Write your first sentence →</Link>
          </Button>
          <Button variant="outline" asChild className="px-6 py-2.5 h-auto text-[14px]">
            <a href="#how-it-works">See how it works ↓</a>
          </Button>
        </div>
      </FadeIn>

      <FadeIn delay={0.27} duration={0.4}>
        <p className="relative font-mono text-[12px] font-medium tracking-widest text-foreground/45">
          open source · no tracking · self-hostable
        </p>
      </FadeIn>

      {/* Floating demo card */}
      <motion.div
        className="relative w-full max-w-[580px] mt-4 text-left rounded-xl border border-border bg-card"
        style={{
          boxShadow:
            '0 0 0 1px rgba(99,102,241,0.08), 0 32px 64px -32px rgba(0,0,0,0.6), 0 0 40px -10px rgba(99,102,241,0.1)',
        }}
        initial={{ opacity: 0, y: 28, filter: 'blur(8px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        transition={{ delay: 0.32, duration: 0.5, ease: EASE }}
      >
        <div className="flex items-center gap-1.5 px-4 py-3 border-b border-border">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
          <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Italian · imperfetto · leggere
          </span>
        </div>
        <div className="px-6 py-5 flex flex-col gap-3">
          <p
            className="leading-relaxed text-foreground"
            style={{ fontSize: 'clamp(1.1rem, 2vw, 1.35rem)' }}
          >
            Da bambino,{' '}
            <span
              className="font-mono text-[0.92em] text-[#a78bfa] px-0.5"
              style={{ borderBottom: '2px solid var(--primary)' }}
            >
              leggevo
            </span>
            {' '}ogni sera fino a mezzanotte.
          </p>
          <p className="text-[0.875rem] text-muted-foreground italic">
            "As a boy, I used to read every evening until midnight."
          </p>
          <div className="flex gap-1.5 flex-wrap pt-3 border-t border-border">
            <HeroChip>new word</HeroChip>
            <HeroChip>interval · 6h</HeroChip>
            <HeroChip accent>✓ correct · next review tomorrow</HeroChip>
          </div>
        </div>
      </motion.div>
    </section>
  );
}

function HeroChip({
  children,
  accent,
}: {
  children: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        'font-mono text-[10px] tracking-widest uppercase rounded-sm',
        accent
          ? 'border-indigo-700 text-indigo-400 bg-indigo-500/5'
          : 'border-border text-muted-foreground',
      )}
    >
      {children}
    </Badge>
  );
}
