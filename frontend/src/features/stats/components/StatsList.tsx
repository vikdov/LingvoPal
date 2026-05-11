import type { HardestItem } from '../types/stats.types';

interface Props {
  items: HardestItem[];
  limit?: number;
}

export function StatsList({ items, limit = 8 }: Props) {
  const visible = items.slice(0, limit);

  if (visible.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4 text-center">
        No data yet — practice more to see which words are hardest.
      </p>
    );
  }

  return (
    <div className="flex flex-col divide-y divide-border">
      {visible.map((item) => {
        const failPct = Math.round(item.failure_rate * 100);
        return (
          <div key={item.item_id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
            <span className="font-mono text-sm text-foreground w-32 shrink-0 truncate">
              {item.term}
            </span>
            <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-destructive/60 transition-all"
                style={{ width: `${failPct}%` }}
              />
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="font-mono text-[11px] text-destructive/80 w-8 text-right">
                {failPct}%
              </span>
              <span className="font-mono text-[10px] text-muted-foreground w-16 text-right">
                {item.total_reviews}rev
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
