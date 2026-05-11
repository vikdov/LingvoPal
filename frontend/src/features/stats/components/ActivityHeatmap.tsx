import { TooltipProvider, Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { DailyStats } from '../types/stats.types';

interface Props {
  data: DailyStats[];
  days?: number;
}

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function buildCells(days: number, reviewMap: Map<string, number>) {
  const cells: { date: string; count: number }[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const iso = d.toISOString().slice(0, 10);
    cells.push({ date: iso, count: reviewMap.get(iso) ?? 0 });
  }
  return cells;
}

function intensityClass(count: number, max: number): string {
  if (count === 0) return 'bg-muted';
  const pct = count / max;
  if (pct < 0.25) return 'bg-primary/30';
  if (pct < 0.5)  return 'bg-primary/55';
  if (pct < 0.75) return 'bg-primary/80';
  return 'bg-primary';
}

export function ActivityHeatmap({ data, days = 84 }: Props) {
  const reviewMap = new Map<string, number>();
  for (const d of data) {
    reviewMap.set(d.stat_date, (reviewMap.get(d.stat_date) ?? 0) + d.total_reviews);
  }

  const max = Math.max(...Array.from(reviewMap.values()), 1);
  const cells = buildCells(days, reviewMap);
  const weeks = Math.ceil(days / 7);

  return (
    <TooltipProvider delayDuration={100}>
      <div className="flex gap-1 overflow-x-auto pb-1">
        <div className="flex flex-col justify-between pr-1 pt-[3px]">
          {DAY_LABELS.map((d) => (
            <span key={d} className="font-mono text-[9px] text-muted-foreground leading-none h-3">
              {d}
            </span>
          ))}
        </div>
        {Array.from({ length: weeks }, (_, wi) => (
          <div key={wi} className="flex flex-col gap-1">
            {Array.from({ length: 7 }, (_, di) => {
              const idx = wi * 7 + di;
              const cell = cells[idx];
              if (!cell) return <div key={di} className="w-3 h-3" />;
              return (
                <Tooltip key={di}>
                  <TooltipTrigger asChild>
                    <div
                      className={`w-3 h-3 rounded-sm cursor-default transition-opacity hover:opacity-80 ${intensityClass(cell.count, max)}`}
                    />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="font-mono text-xs">
                    {cell.date}: {cell.count} review{cell.count !== 1 ? 's' : ''}
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
}
