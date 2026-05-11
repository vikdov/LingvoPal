import { Badge } from '@/components/ui/badge';
import { BentoItem } from '@/components/ui/cybernetic-bento-grid';
import { Separator } from '@/components/ui/separator';
import { motion } from 'motion/react';

const STATS = [
  { label: 'Day streak', value: '14' },
  { label: 'Words learned', value: '312' },
  { label: 'Retention rate', value: '87%' },
  { label: 'Next review', value: '6 h' },
];

const ACTIVITY = [4, 7, 3, 9, 6, 11, 8, 5, 12, 7, 9, 14, 10, 8];
const MAX_ACTIVITY = Math.max(...ACTIVITY);

export function ProgressSection() {
  return (
    <section className="flex flex-col items-center gap-10 px-6 py-20 border-t border-border bg-muted/40">
      <div className="flex flex-col items-center gap-3 text-center">
        <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
          <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> Progress
        </Badge>
        <h2
          className="font-bold tracking-[-0.03em] text-foreground"
          style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
        >
          Progress you can actually measure.
        </h2>
        <p className="text-[0.9375rem] text-muted-foreground max-w-[40ch] leading-relaxed">
          No coins. No trophies. Just words retained, reviews done, and accuracy over time.
        </p>
      </div>

      <div className="w-full max-w-[860px] flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground/60 italic">
            Example dashboard
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map(({ label, value }) => (
            <BentoItem key={label} className="flex flex-col gap-1">
              <span
                className="font-bold tracking-[-0.03em] text-foreground"
                style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
              >
                {value}
              </span>
              <span className="text-[0.75rem] font-mono uppercase tracking-widest text-muted-foreground/70">
                {label}
              </span>
            </BentoItem>
          ))}
        </div>

        <BentoItem className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <span className="text-[0.8125rem] font-semibold text-foreground">Reviews last 14 days</span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">113 total</span>
          </div>
          <Separator />
          <div className="flex items-end gap-1.5 h-16">
            {ACTIVITY.map((count, i) => (
              <motion.div
                key={i}
                className="flex-1 rounded-sm bg-primary/70"
                style={{ transformOrigin: 'bottom', height: `${(count / MAX_ACTIVITY) * 100}%`, minHeight: '4px' }}
                initial={{ scaleY: 0 }}
                whileInView={{ scaleY: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: i * 0.04, ease: 'easeOut' }}
                title={`${count} reviews`}
              />
            ))}
          </div>
          <div className="flex justify-between">
            <span className="font-mono text-[10px] text-muted-foreground">14 days ago</span>
            <span className="font-mono text-[10px] text-muted-foreground">today</span>
          </div>
        </BentoItem>
      </div>
    </section>
  );
}
