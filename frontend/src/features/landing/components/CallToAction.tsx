import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FadeUp } from '@/components/ui/animate';

export function CallToAction() {
  return (
    <section className="relative flex flex-col items-center text-center gap-7 px-6 py-36 overflow-hidden border-t border-border bg-card">
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
            'radial-gradient(ellipse 90% 80% at 50% 50%, black 30%, transparent 100%)',
        }}
      />
      {/* Top glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute top-0 left-0 right-0 flex justify-center"
      >
        <div
          style={{
            width: '600px',
            height: '280px',
            background: 'radial-gradient(ellipse, rgba(99,102,241,0.22) 0%, rgba(139,92,246,0.1) 40%, transparent 70%)',
            transform: 'translateY(-40%)',
          }}
        />
      </div>
      {/* Bottom glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-0 right-0 flex justify-center"
      >
        <div
          style={{
            width: '600px',
            height: '280px',
            background: 'radial-gradient(ellipse, rgba(99,102,241,0.18) 0%, rgba(139,92,246,0.08) 40%, transparent 70%)',
            transform: 'translateY(40%)',
          }}
        />
      </div>

      <FadeUp>
        <Badge variant="outline" className="relative font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
          <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> Get started
        </Badge>
      </FadeUp>

      <FadeUp delay={0.07}>
        <h2
          className="relative font-bold tracking-[-0.03em] leading-tight text-foreground max-w-[20ch]"
          style={{ fontSize: 'clamp(2rem, 4vw, 3rem)' }}
        >
          A language isn't learned.{' '}
          <span className="bg-gradient-to-r from-sky-400 via-indigo-400 to-indigo-600 bg-clip-text text-transparent">
            It's written into you.
          </span>
        </h2>
      </FadeUp>

      <FadeUp delay={0.13}>
        <p className="relative text-[0.9375rem] text-muted-foreground">
          One sentence at a time. No credit card. No commitment.
        </p>
      </FadeUp>

      <FadeUp delay={0.19}>
        <Button
          asChild
          className="relative px-7 py-3 h-auto text-[15px]"
          style={{ boxShadow: '0 0 40px -8px rgba(99,102,241,0.7), 0 0 80px -20px rgba(139,92,246,0.4)' }}
        >
          <Link to="/auth/register">Start your first recall session →</Link>
        </Button>
      </FadeUp>

      <FadeUp delay={0.24}>
        <p className="relative font-mono text-[11px] tracking-widest uppercase text-muted-foreground">
          free · self-hostable · no tracking · open source
        </p>
      </FadeUp>

      <FadeUp delay={0.3}>
        <p
          className="relative font-bold tracking-[-0.02em] text-center text-foreground/40 max-w-[28ch] mt-4 border-t border-border pt-8"
          style={{ fontSize: 'clamp(1rem, 2vw, 1.25rem)' }}
        >
          "A language isn't memorized. It's practiced into existence."
        </p>
      </FadeUp>
    </section>
  );
}
