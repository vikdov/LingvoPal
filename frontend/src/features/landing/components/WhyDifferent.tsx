import { XIcon, CheckIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { BentoItem } from '@/components/ui/cybernetic-bento-grid';
import { Separator } from '@/components/ui/separator';
import { FadeUp } from '@/components/ui/animate';

const THEIRS = [
  'Multiple choice — pick the right answer',
  'Passive exposure, not active retrieval',
  'Tap a picture, get a reward',
  'Gamified streaks that punish absence',
  'Words out of context',
];

const OURS = [
  'Type from memory, every session',
  'Active recall wires words permanently',
  'Write in real sentences, every time',
  'Reviews scheduled when science says so',
  'Context-first — sentence before word',
];

export function WhyDifferent() {
  return (
    <section className="flex flex-col items-center gap-10 px-6 py-20 border-t border-border bg-muted/40">
      <FadeUp>
        <div className="flex flex-col items-center gap-3 text-center">
          <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
            <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> The difference
          </Badge>
          <h2
            className="font-bold tracking-[-0.03em] text-foreground"
            style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
          >
            Recognition is not recall.
          </h2>
          <p className="text-[0.9375rem] text-muted-foreground max-w-[42ch] leading-relaxed">
            Most apps train you to recognize words when you see them. That's not the same as being able to produce them.
          </p>
        </div>
      </FadeUp>

      <FadeUp delay={0.1}>
      <div className="w-full max-w-[860px] grid grid-cols-1 md:grid-cols-2 gap-4">
        <BentoItem className="flex flex-col gap-3 bg-muted/40">
          <h3 className="text-[0.9375rem] font-semibold text-muted-foreground tracking-[-0.01em]">
            Other language apps
          </h3>
          <Separator />
          <div className="flex flex-col gap-3">
            {THEIRS.map((item) => (
              <div key={item} className="flex items-start gap-2.5">
                <XIcon className="size-3.5 shrink-0 mt-0.5 text-destructive/60" />
                <span className="text-[0.8125rem] text-muted-foreground leading-snug">{item}</span>
              </div>
            ))}
          </div>
        </BentoItem>

        <BentoItem
          className="flex flex-col gap-3 border-primary/20"
          style={{ boxShadow: '0 0 0 1px oklch(from var(--primary) l c h / 0.08), 0 8px 32px -8px oklch(from var(--primary) l c h / 0.12)' }}
        >
          <h3 className="text-[0.9375rem] font-semibold text-foreground tracking-[-0.01em]">
            LingvoPal
          </h3>
          <Separator />
          <div className="flex flex-col gap-3">
            {OURS.map((item) => (
              <div key={item} className="flex items-start gap-2.5">
                <CheckIcon className="size-3.5 shrink-0 mt-0.5 text-primary" />
                <span className="text-[0.8125rem] text-foreground leading-snug">{item}</span>
              </div>
            ))}
          </div>
        </BentoItem>
      </div>
      </FadeUp>
    </section>
  );
}
