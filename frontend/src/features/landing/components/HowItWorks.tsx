import { Badge } from '@/components/ui/badge';
import { BentoHoverItem } from '@/components/ui/cybernetic-bento-grid';
import { FadeUp } from '@/components/ui/animate';

const STEPS = [
  {
    num: '01',
    title: 'Add your vocabulary',
    body: 'Import a word, phrase, or conjugation. Pair it with a real sentence.',
    example: 'gehen → Ich gehe jeden Tag zur Arbeit.',
  },
  {
    num: '02',
    title: 'Practice in context',
    body: 'Fill the gap. Type from memory, letter by letter. No hints. No word bank.',
    example: 'Ich ___ jeden Tag zur Arbeit.\nYou type: gehe',
  },
  {
    num: '03',
    title: 'SM-2 schedules the rest',
    body: 'Your ease and lapse history shape when you see it again. Optimal spacing, automatic.',
    example: '6h → 1d → 3d → 9d → …',
  },
] as const;

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="flex flex-col items-center gap-12 px-6 py-20 border-t border-border"
    >
      <FadeUp>
        <div className="flex flex-col items-center gap-3 text-center">
          <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
            <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> The method
          </Badge>
          <h2
            className="font-bold tracking-[-0.03em] text-foreground"
            style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
          >
            Three steps. One habit.
          </h2>
          <p className="text-[0.9375rem] text-muted-foreground max-w-[40ch] leading-relaxed">
            No passive review. No tapping pictures. Just writing — the way your brain actually learns.
          </p>
        </div>
      </FadeUp>

      <FadeUp delay={0.08}>
      <div
        className="w-full max-w-[860px] rounded-xl overflow-hidden border border-border"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          background: 'var(--border)',
          gap: '1px',
        }}
      >
        {STEPS.map((step) => (
          <BentoHoverItem
            key={step.num}
            className="flex flex-col gap-3 p-7 bg-background"
          >
            <div className="flex items-center gap-2 font-mono text-[11px] tracking-widest uppercase text-primary">
              <span aria-hidden className="w-6 h-px bg-primary opacity-40" />
              {step.num}
            </div>
            <h3 className="font-semibold tracking-[-0.02em] text-foreground text-[1.0625rem]">
              {step.title}
            </h3>
            <p className="text-[0.875rem] text-muted-foreground leading-relaxed">
              {step.body}
            </p>
            <pre className="mt-1 text-[11px] font-mono text-muted-foreground bg-card border border-border rounded-md p-3 whitespace-pre-wrap leading-relaxed">
              {step.example}
            </pre>
          </BentoHoverItem>
        ))}
      </div>
      </FadeUp>
    </section>
  );
}
