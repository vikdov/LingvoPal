import { BentoItem } from '@/components/ui/cybernetic-bento-grid';
import { Badge } from '@/components/ui/badge';
import { FadeUp } from '@/components/ui/animate';

export function Features() {
  return (
    <section className="flex flex-col items-center gap-10 px-6 py-20 border-t border-border">
      <FadeUp>
        <div className="flex flex-col items-center gap-3 text-center">
          <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
            <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> Platform
          </Badge>
          <h2
            className="font-bold tracking-[-0.03em] text-foreground"
            style={{ fontSize: 'clamp(2rem, 3.5vw, 2.75rem)' }}
          >
            Everything you need to stay consistent.
          </h2>
        </div>
      </FadeUp>

      <FadeUp delay={0.1}>
      <div className="bento-grid w-full max-w-5xl">
        <BentoItem className="col-span-2 row-span-2 flex flex-col gap-4">
          <h3 className="text-xl font-semibold tracking-[-0.02em] text-foreground">Build your own vocabulary sets</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Create sets from words you actually encounter — in books, podcasts, conversations.
            Pair each word with a real sentence so context is always there.
          </p>
          <pre className="mt-auto text-[11px] font-mono text-muted-foreground bg-background border border-border rounded-md p-3 whitespace-pre-wrap leading-relaxed">
{`+ New item
  Word:     leggevo
  Sentence: Da bambino, ___ ogni sera.
  Lang:     Italian → English`}
          </pre>
        </BentoItem>

        <BentoItem className="flex flex-col gap-2">
          <h3 className="text-base font-semibold text-foreground">Any language</h3>
          <p className="text-sm text-muted-foreground">Italian, French, German, Japanese — study whatever you're learning.</p>
        </BentoItem>

        <BentoItem className="flex flex-col gap-2">
          <h3 className="text-base font-semibold text-foreground">Daily streak</h3>
          <p className="text-sm text-muted-foreground">A review queue appears every day. Short sessions compound over months.</p>
        </BentoItem>

        <BentoItem className="row-span-2 flex flex-col gap-2">
          <h3 className="text-base font-semibold text-foreground">Progress insights</h3>
          <p className="text-sm text-muted-foreground">See retention rates, lapsed cards, and daily review counts. Know exactly where you stand.</p>
        </BentoItem>

        <BentoItem className="col-span-2 flex flex-col gap-2">
          <h3 className="text-base font-semibold text-foreground">Discover community sets</h3>
          <p className="text-sm text-muted-foreground">Browse curated vocabulary sets shared by other learners. Clone and customize to fit your goals.</p>
        </BentoItem>

        <BentoItem className="flex flex-col gap-2">
          <h3 className="text-base font-semibold text-foreground">Free & open source</h3>
          <p className="text-sm text-muted-foreground">No subscription. Self-host it. Your data stays yours.</p>
        </BentoItem>
      </div>
      </FadeUp>
    </section>
  );
}
