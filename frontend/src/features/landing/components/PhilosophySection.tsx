import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

const PRINCIPLES = [
  {
    over: 'Writing',
    under: 'tapping',
    body: 'Producing a word from memory builds stronger connections than recognizing it from a list. Every session asks you to write.',
  },
  {
    over: 'Recall',
    under: 'recognition',
    body: 'You might recognize leggevo on a flashcard and still blank on it mid-sentence. Recall is harder, and that\'s exactly the point.',
  },
  {
    over: 'Depth',
    under: 'speed',
    body: 'One word remembered six months from now is worth more than twenty you half-learned this week. Spacing beats cramming.',
  },
  {
    over: 'Focus',
    under: 'distraction',
    body: 'No coins, no levels, no streaks that shame you. A tool that does one thing and does it with full seriousness.',
  },
];

export function PhilosophySection() {
  return (
    <section className="flex flex-col items-center gap-12 px-6 py-20 border-t border-border bg-muted/40">
      <div className="flex flex-col items-center gap-3 text-center">
        <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
          <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> Philosophy
        </Badge>
        <h2
          className="font-bold tracking-[-0.03em] text-foreground"
          style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
        >
          Built on a single belief.
        </h2>
        <p className="text-[0.9375rem] text-muted-foreground max-w-[42ch] leading-relaxed">
          You remember what you've had to retrieve. Everything else is just exposure.
        </p>
      </div>

      <div className="w-full max-w-[860px] flex flex-col divide-y divide-border">
        {PRINCIPLES.map(({ over, under, body }) => (
          <div key={over} className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-4 py-8 first:pt-0 last:pb-0">
            <div className="flex items-baseline gap-2 flex-wrap">
              <span
                className="font-bold tracking-[-0.03em] text-foreground"
                style={{ fontSize: 'clamp(1.25rem, 2vw, 1.5rem)' }}
              >
                {over}
              </span>
              <span className="text-[0.875rem] font-mono text-muted-foreground">
                over {under}
              </span>
            </div>
            <p className="text-[0.9375rem] text-muted-foreground leading-relaxed">
              {body}
            </p>
          </div>
        ))}
      </div>

      <Separator className="w-full max-w-[860px]" />

      <p
        className="font-bold tracking-[-0.03em] text-center text-foreground/80 max-w-[28ch]"
        style={{ fontSize: 'clamp(1.25rem, 2.5vw, 1.75rem)' }}
      >
        "A language isn't memorized. It's practiced into existence."
      </p>
    </section>
  );
}
