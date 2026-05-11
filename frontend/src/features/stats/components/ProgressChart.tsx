import { motion } from 'motion/react';
import { TooltipProvider, Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { DailyStats } from '../types/stats.types';

interface Props {
  data: DailyStats[];
  days?: number;
}

function buildCells(days: number, data: DailyStats[]) {
  const map = new Map<string, { correct: number; incorrect: number }>();
  for (const d of data) {
    const existing = map.get(d.stat_date);
    map.set(d.stat_date, {
      correct: (existing?.correct ?? 0) + d.correct_count,
      incorrect: (existing?.incorrect ?? 0) + d.incorrect_count,
    });
  }
  const cells: { date: string; correct: number; incorrect: number; total: number }[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const iso = d.toISOString().slice(0, 10);
    const entry = map.get(iso);
    cells.push({
      date: iso,
      correct: entry?.correct ?? 0,
      incorrect: entry?.incorrect ?? 0,
      total: (entry?.correct ?? 0) + (entry?.incorrect ?? 0),
    });
  }
  return cells;
}

export function ProgressChart({ data, days = 14 }: Props) {
  const cells = buildCells(days, data);
  const maxTotal = Math.max(...cells.map((c) => c.total), 1);

  return (
    <TooltipProvider delayDuration={100}>
      <div className="flex items-end gap-1 h-14">
        {cells.map((cell, i) => {
          const totalPct = cell.total / maxTotal;
          const barHeight = Math.max(totalPct * 100, cell.total > 0 ? 8 : 2);
          const correctPct = cell.total > 0 ? cell.correct / cell.total : 0;
          const label = new Date(cell.date + 'T00:00:00').toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          });
          return (
            <Tooltip key={cell.date}>
              <TooltipTrigger asChild>
                <div
                  className="flex-1 flex flex-col-reverse rounded-sm overflow-hidden cursor-default"
                  style={{ height: `${barHeight}%` }}
                >
                  <motion.div
                    className="w-full bg-primary/70"
                    initial={{ scaleY: 0 }}
                    whileInView={{ scaleY: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.3, delay: i * 0.025, ease: 'easeOut' }}
                    style={{ transformOrigin: 'bottom', height: `${correctPct * 100}%` }}
                  />
                  {cell.incorrect > 0 && (
                    <motion.div
                      className="w-full bg-destructive/40"
                      initial={{ scaleY: 0 }}
                      whileInView={{ scaleY: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.3, delay: i * 0.025, ease: 'easeOut' }}
                      style={{ transformOrigin: 'bottom', height: `${(1 - correctPct) * 100}%` }}
                    />
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="font-mono text-xs">
                <p>{label}</p>
                {cell.total === 0 ? (
                  <p className="text-muted-foreground">No reviews</p>
                ) : (
                  <>
                    <p className="text-primary">{cell.correct} correct</p>
                    {cell.incorrect > 0 && (
                      <p className="text-destructive">{cell.incorrect} incorrect</p>
                    )}
                  </>
                )}
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
      <div className="flex justify-between mt-1.5">
        <span className="font-mono text-[9px] text-muted-foreground">
          {new Date(cells[0].date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-mono text-[9px] text-muted-foreground">
            <span className="inline-block w-2 h-2 rounded-sm bg-primary/70" /> correct
          </span>
          <span className="flex items-center gap-1 font-mono text-[9px] text-muted-foreground">
            <span className="inline-block w-2 h-2 rounded-sm bg-destructive/40" /> incorrect
          </span>
        </div>
        <span className="font-mono text-[9px] text-muted-foreground">today</span>
      </div>
    </TooltipProvider>
  );
}
